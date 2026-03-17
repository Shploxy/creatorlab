from __future__ import annotations

import math
import threading
import time
import urllib.request
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from app.core.config import settings
from app.core.exceptions import ValidationError
from app.core.runtime import get_runtime_info
from app.core.storage import storage
from app.services.types import JobContext, OutputArtifact

_UPSAMPLERS: dict[str, object] = {}
_UPSAMPLER_LOCK = threading.Lock()

LIGHTWEIGHT_MODE = "standard"
HEAVY_MODE = "high_quality"


def _ensure_weights(model_name: str, weights_url: str) -> Path:
    models_dir = storage.root / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    weights_path = models_dir / f"{model_name}.pth"
    if not weights_path.exists():
        urllib.request.urlretrieve(weights_url, weights_path)
    return weights_path


def _build_realesrganer(mode: str):
    try:
        import torchvision.transforms._functional_tensor as functional_tensor

        sys.modules.setdefault("torchvision.transforms.functional_tensor", functional_tensor)
    except Exception:
        pass

    from basicsr.archs.rrdbnet_arch import RRDBNet
    from realesrgan import RealESRGANer

    runtime = get_runtime_info()
    if mode == HEAVY_MODE:
        model_name = settings.realesrgan_model_name
        weights_url = settings.realesrgan_weights_url
        scale = 4
        tile = 256 if runtime["cuda_available"] else 128
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
    else:
        model_name = settings.lightweight_ai_model_name
        weights_url = settings.lightweight_ai_weights_url
        scale = 2
        tile = 192 if runtime["cuda_available"] else 96
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=2)

    weights_path = _ensure_weights(model_name, weights_url)
    return RealESRGANer(
        scale=scale,
        model_path=str(weights_path),
        model=model,
        tile=tile,
        tile_pad=12,
        pre_pad=0,
        half=bool(runtime["cuda_available"]),
        gpu_id=0 if runtime["cuda_available"] else None,
    )


def _get_realesrganer(mode: str):
    cache_key = f"{mode}:{get_runtime_info()['device']}"
    with _UPSAMPLER_LOCK:
        if cache_key in _UPSAMPLERS:
            return _UPSAMPLERS[cache_key]
        upsampler = _build_realesrganer(mode)
        _UPSAMPLERS[cache_key] = upsampler
        return upsampler


def _resolve_mode(context: JobContext, runtime: dict[str, bool | str]) -> tuple[str, int, str]:
    requested_mode = str(context.options.get("quality_mode", LIGHTWEIGHT_MODE) or LIGHTWEIGHT_MODE)
    requested_scale = int(context.options.get("scale", 2) or 2)

    if requested_mode == HEAVY_MODE:
        if not settings.enable_heavy_ai:
            return LIGHTWEIGHT_MODE, 2, "Heavy AI mode is disabled on this deployment, so Standard AI was used."
        if not runtime["cuda_available"]:
            return LIGHTWEIGHT_MODE, 2, "High Quality AI requires more resources, so Standard AI was used on CPU."
        return HEAVY_MODE, 4, ""

    return LIGHTWEIGHT_MODE, min(max(requested_scale, 2), 2), ""


def _preprocess_image(image: Image.Image) -> tuple[Image.Image, dict[str, int | bool]]:
    width, height = image.size
    pixels = width * height
    resized_for_ai = False

    if max(width, height) > settings.upscale_max_edge:
        ratio = settings.upscale_max_edge / max(width, height)
        width = max(1, int(width * ratio))
        height = max(1, int(height * ratio))
        image = image.resize((width, height), Image.Resampling.LANCZOS)
        pixels = width * height
        resized_for_ai = True

    if pixels > settings.upscale_max_input_pixels:
        ratio = math.sqrt(settings.upscale_max_input_pixels / float(pixels))
        width = max(1, int(width * ratio))
        height = max(1, int(height * ratio))
        image = image.resize((width, height), Image.Resampling.LANCZOS)
        resized_for_ai = True

    return image, {
        "ai_input_width": image.width,
        "ai_input_height": image.height,
        "resized_for_ai": resized_for_ai,
    }


def _enhance_with_fallback(image: Image.Image, scale: int) -> Image.Image:
    original_mode = "RGBA" if "A" in image.getbands() else "RGB"
    prepared = image.convert(original_mode)
    upscaled = prepared.resize((image.width * scale, image.height * scale), Image.Resampling.LANCZOS)
    if upscaled.mode == "RGBA":
        rgb = Image.merge("RGB", upscaled.split()[:3])
        alpha = upscaled.getchannel("A")
        rgb = ImageOps.autocontrast(rgb, cutoff=0.5)
        rgb = ImageEnhance.Contrast(rgb).enhance(1.05)
        rgb = rgb.filter(ImageFilter.DETAIL)
        rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.5, percent=125, threshold=3))
        enhanced = rgb.convert("RGBA")
        enhanced.putalpha(alpha)
        return enhanced

    enhanced = ImageOps.autocontrast(upscaled, cutoff=0.5)
    enhanced = ImageEnhance.Contrast(enhanced).enhance(1.05)
    enhanced = enhanced.filter(ImageFilter.DETAIL)
    return enhanced.filter(ImageFilter.UnsharpMask(radius=1.5, percent=125, threshold=3))


def process_upscale(context: JobContext) -> list[OutputArtifact]:
    started_at = time.monotonic()
    source = context.file_paths[0]
    destination = source.with_name(f"{source.stem}_upscaled.png")
    runtime = get_runtime_info()
    mode, scale, mode_message = _resolve_mode(context, runtime)
    engine = "fallback"

    with Image.open(source) as original_image:
        source_width, source_height = original_image.width, original_image.height
        prepared_image, prep_meta = _preprocess_image(original_image)
        estimated_pixels = prepared_image.width * prepared_image.height * scale * scale
        if not runtime["cuda_available"] and estimated_pixels > settings.upscale_max_input_pixels * 4:
            raise ValidationError(
                "This image is too large for stable AI upscaling on CPU. Try a smaller image or use Standard AI mode."
            )

        try:
            upsampler = _get_realesrganer(mode)
            rgb_image = prepared_image.convert("RGB")
            rgb_array = np.array(rgb_image)
            enhanced_bgr, _ = upsampler.enhance(rgb_array[:, :, ::-1], outscale=scale)
            enhanced = Image.fromarray(enhanced_bgr[:, :, ::-1])
            if "A" in original_image.getbands():
                alpha_source = prepared_image.getchannel("A") if "A" in prepared_image.getbands() else original_image.getchannel("A")
                alpha = alpha_source.resize(enhanced.size, Image.Resampling.LANCZOS)
                enhanced = enhanced.convert("RGBA")
                enhanced.putalpha(alpha)
            engine = settings.realesrgan_model_name if mode == HEAVY_MODE else settings.lightweight_ai_model_name
        except Exception:
            enhanced = _enhance_with_fallback(prepared_image, scale)
            mode_message = mode_message or "AI weights were unavailable, so CreatorLab used a lightweight enhancement fallback."

        elapsed = time.monotonic() - started_at
        if elapsed > settings.upscale_timeout_seconds:
            raise ValidationError(
                "Upscaling took too long for the current machine. Try Standard AI mode or a smaller image."
            )
        enhanced.save(destination, format="PNG")

    return [
        OutputArtifact(
            path=destination,
            content_type="image/png",
            filename=destination.name,
            meta={
                "width": scale * prep_meta["ai_input_width"],
                "height": scale * prep_meta["ai_input_height"],
                "source_width": source_width,
                "source_height": source_height,
                "scale": scale,
                "engine": engine,
                "device": str(runtime["device"]),
                "quality_mode": mode,
                "resized_for_ai": prep_meta["resized_for_ai"],
                "ai_input_width": prep_meta["ai_input_width"],
                "ai_input_height": prep_meta["ai_input_height"],
                "processing_seconds": round(elapsed, 2),
                "mode_message": mode_message or None,
            },
        )
    ]
