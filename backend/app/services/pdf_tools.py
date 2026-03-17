from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.core.exceptions import ValidationError
from app.core.config import settings
from app.core.storage import storage
from app.services.types import JobContext, OutputArtifact


def _parse_page_ranges(ranges: str, total_pages: int) -> tuple[list[int], int]:
    chunks = [item.strip() for item in ranges.split(",") if item.strip()]
    if not chunks:
        raise ValidationError("Enter a page range to extract a PDF segment.")

    selected_pages: list[int] = []
    for chunk in chunks:
        try:
            if "-" in chunk:
                start_str, end_str = chunk.split("-", maxsplit=1)
                start = int(start_str)
                end = int(end_str)
                if start <= 0 or end <= 0 or end < start:
                    raise ValidationError(f"Invalid page range '{chunk}'.")
                pages = range(start - 1, end)
            else:
                page = int(chunk)
                if page <= 0:
                    raise ValidationError(f"Invalid page '{chunk}'.")
                pages = [page - 1]
        except ValueError as exc:
            raise ValidationError(f"Invalid page range value '{chunk}'.") from exc

        for page_index in pages:
            if page_index < 0 or page_index >= total_pages:
                raise ValidationError(f"Page index out of range in chunk '{chunk}'.")
            selected_pages.append(page_index)

    if len(selected_pages) > settings.max_pdf_pages:
        raise ValidationError(f"Selected output exceeds the {settings.max_pdf_pages}-page safety limit.")
    return selected_pages, len(selected_pages)


def process_pdf_merge(context: JobContext) -> list[OutputArtifact]:
    writer = PdfWriter()
    destination = context.file_paths[0].with_name(f"{context.job_id}_merged.pdf")
    page_count = 0

    for file_path in context.file_paths:
        reader = PdfReader(str(file_path))
        for page in reader.pages:
            writer.add_page(page)
            page_count += 1

    with destination.open("wb") as stream:
        writer.write(stream)

    return [
        OutputArtifact(
            path=destination,
            content_type="application/pdf",
            filename=destination.name,
            meta={"page_count": page_count},
        )
    ]


def process_pdf_split(context: JobContext) -> list[OutputArtifact]:
    source = context.file_paths[0]
    reader = PdfReader(str(source))
    requested_mode = str(context.options.get("mode") or context.options.get("split_mode", "extract_range")).strip().lower()
    split_mode = {
        "range": "extract_range",
        "extract_range": "extract_range",
        "extract": "extract_range",
        "chunks": "split_chunks",
        "chunk": "split_chunks",
        "split_chunks": "split_chunks",
    }.get(requested_mode, "extract_range")
    ranges = str(context.options.get("page_ranges", "")).strip()
    try:
        chunk_size = int(str(context.options.get("chunk_size", "2") or "2"))
    except ValueError:
        chunk_size = 2
    if chunk_size <= 0:
        chunk_size = 2

    outputs: list[OutputArtifact] = []

    if split_mode == "split_chunks":
        total_pages = len(reader.pages)
        if total_pages == 0:
            raise ValidationError("The uploaded PDF does not contain any pages.")
        part_count = (total_pages + chunk_size - 1) // chunk_size
        if part_count > settings.max_pdf_split_outputs:
            raise ValidationError(
                f"Chunk splitting would create too many files. Limit is {settings.max_pdf_split_outputs} outputs per job."
            )
        part_paths: list[Path] = []
        for index, start in enumerate(range(0, total_pages, chunk_size), start=1):
            writer = PdfWriter()
            end = min(start + chunk_size, total_pages)
            for page_index in range(start, end):
                writer.add_page(reader.pages[page_index])

            destination = source.with_name(f"{source.stem}_part_{index}.pdf")
            with destination.open("wb") as stream:
                writer.write(stream)
            part_paths.append(destination)
            outputs.append(
                OutputArtifact(
                    path=destination,
                    content_type="application/pdf",
                    filename=destination.name,
                    meta={
                        "page_count": end - start,
                        "part_index": index,
                        "chunk_size": chunk_size,
                        "split_mode": split_mode,
                        "mode": "chunks",
                    },
                )
            )

        if len(part_paths) > 1:
            zip_destination = source.with_name(f"{source.stem}_split_parts.zip")
            with ZipFile(zip_destination, "w", compression=ZIP_DEFLATED) as bundle:
                for part_path in part_paths:
                    bundle.write(part_path, arcname=part_path.name)
            outputs.append(
                OutputArtifact(
                    path=zip_destination,
                    content_type="application/zip",
                    filename=zip_destination.name,
                    meta={
                        "bundle": True,
                        "file_count": len(part_paths),
                        "chunk_size": chunk_size,
                        "split_mode": split_mode,
                        "mode": "chunks",
                    },
                )
            )
        return outputs

    if not ranges:
        raise ValidationError("Enter a page range to extract a PDF segment.")

    writer = PdfWriter()
    page_indexes, page_total = _parse_page_ranges(ranges, len(reader.pages))
    for page_index in page_indexes:
        writer.add_page(reader.pages[page_index])

    destination = source.with_name(f"{source.stem}_extracted.pdf")
    with destination.open("wb") as stream:
        writer.write(stream)
    outputs.append(
        OutputArtifact(
            path=destination,
            content_type="application/pdf",
            filename=destination.name,
            meta={"page_count": page_total, "range": ranges, "split_mode": split_mode, "mode": "range"},
        )
    )
    return outputs


def process_images_to_pdf(context: JobContext) -> list[OutputArtifact]:
    destination = context.file_paths[0].with_name(f"{context.job_id}_images.pdf")
    packet = BytesIO()
    page_canvas = canvas.Canvas(packet, pagesize=letter)

    for image_path in context.file_paths:
        with Image.open(image_path) as image:
            width, height = image.size
            page_width, page_height = letter
            scale = min(page_width / width, page_height / height)
            render_width = width * scale
            render_height = height * scale
            x = (page_width - render_width) / 2
            y = (page_height - render_height) / 2

            tmp = storage.temp_dir / f"{context.job_id}_{image_path.stem}.jpg"
            image.convert("RGB").save(tmp, format="JPEG", quality=92)
            page_canvas.drawImage(str(tmp), x, y, render_width, render_height)
            page_canvas.showPage()
            tmp.unlink(missing_ok=True)

    page_canvas.save()
    destination.write_bytes(packet.getvalue())
    return [
        OutputArtifact(
            path=destination,
            content_type="application/pdf",
            filename=destination.name,
            meta={"page_count": len(context.file_paths)},
        )
    ]
