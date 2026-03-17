from pathlib import Path

from PIL import Image

from app.services.types import JobContext, OutputArtifact


def process_compress(context: JobContext) -> list[OutputArtifact]:
    source = context.file_paths[0]
    original_size = source.stat().st_size

    with Image.open(source) as image:
        if "A" in image.getbands():
            destination = source.with_name(f"{source.stem}_compressed.png")
            quantized = image.convert("RGBA").quantize(colors=192)
            quantized.save(destination, format="PNG", optimize=True)
            content_type = "image/png"
        else:
            destination = source.with_name(f"{source.stem}_compressed.jpg")
            image.convert("RGB").save(destination, format="JPEG", optimize=True, progressive=True, quality=76, subsampling=1)
            content_type = "image/jpeg"

    compressed_size = destination.stat().st_size
    savings = max(0, original_size - compressed_size)
    savings_ratio = round((savings / original_size) * 100, 1) if original_size else 0.0
    return [
        OutputArtifact(
            path=destination,
            content_type=content_type,
            filename=destination.name,
            meta={
                "original_size": original_size,
                "compressed_size": compressed_size,
                "saved_bytes": savings,
                "saved_percent": savings_ratio,
            },
        )
    ]
