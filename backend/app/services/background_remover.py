import threading
from io import BytesIO
from pathlib import Path

from PIL import Image

from app.core.config import settings
from app.services.types import JobContext, OutputArtifact

try:
    from rembg import new_session, remove
except Exception:  # pragma: no cover - optional dependency behavior
    new_session = None
    remove = None

_SESSION = None
_SESSION_LOCK = threading.Lock()


def _get_session():
    global _SESSION
    if remove is None or new_session is None:
        return None
    with _SESSION_LOCK:
        if _SESSION is None:
            _SESSION = new_session(settings.rembg_model_name)
    return _SESSION


def _fallback_remove(source: Path, destination: Path) -> None:
    with Image.open(source).convert("RGBA") as image:
        pixels = image.load()
        width, height = image.size
        samples = [
            pixels[0, 0],
            pixels[width - 1, 0],
            pixels[0, height - 1],
            pixels[width - 1, height - 1],
        ]
        background = tuple(sum(sample[index] for sample in samples) // len(samples) for index in range(3))

        for x in range(width):
            for y in range(height):
                red, green, blue, alpha = pixels[x, y]
                distance = abs(red - background[0]) + abs(green - background[1]) + abs(blue - background[2])
                if distance < 45:
                    pixels[x, y] = (red, green, blue, 0)
                elif distance < 80:
                    softened_alpha = max(0, int(alpha * ((distance - 45) / 35)))
                    pixels[x, y] = (red, green, blue, softened_alpha)
        image.save(destination, format="PNG")


def process_background_remove(context: JobContext) -> list[OutputArtifact]:
    source = context.file_paths[0]
    destination = source.with_name(f"{source.stem}_transparent.png")
    engine = "fallback"

    if remove is not None:
        data = source.read_bytes()
        session = _get_session()
        output = remove(data, session=session)
        image = Image.open(BytesIO(output)).convert("RGBA")
        image.save(destination, format="PNG")
        engine = settings.rembg_model_name
    else:
        _fallback_remove(source, destination)

    return [
        OutputArtifact(
            path=destination,
            content_type="image/png",
            filename=destination.name,
            meta={"engine": engine},
        )
    ]
