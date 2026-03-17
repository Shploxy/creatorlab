from __future__ import annotations

import json
import mimetypes
import os
import time
import http.cookiejar
import urllib.error
import urllib.request
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageDraw
from pypdf import PdfReader, PdfWriter


ROOT = Path(__file__).resolve().parents[1]
TMP_DIR = ROOT / "storage" / "smoke"
BASE_URL = os.environ.get("CREATORLAB_BASE_URL", "http://127.0.0.1:8000")
COOKIE_JAR = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(COOKIE_JAR))


def _request(method: str, path: str, data: bytes | None = None, headers: dict[str, str] | None = None) -> tuple[int, bytes]:
    request = urllib.request.Request(f"{BASE_URL}{path}", data=data, headers=headers or {}, method=method)
    try:
        with OPENER.open(request, timeout=60) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def _multipart(fields: dict[str, str], files: list[tuple[str, Path]]) -> tuple[bytes, str]:
    boundary = f"----CreatorLabBoundary{uuid4().hex}"
    body = BytesIO()

    for key, value in fields.items():
        body.write(f"--{boundary}\r\n".encode())
        body.write(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
        body.write(value.encode())
        body.write(b"\r\n")

    for field_name, path in files:
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        body.write(f"--{boundary}\r\n".encode())
        body.write(
            f'Content-Disposition: form-data; name="{field_name}"; filename="{path.name}"\r\n'.encode()
        )
        body.write(f"Content-Type: {mime_type}\r\n\r\n".encode())
        body.write(path.read_bytes())
        body.write(b"\r\n")

    body.write(f"--{boundary}--\r\n".encode())
    return body.getvalue(), boundary


def _json(path: str) -> dict:
    status, payload = _request("GET", path)
    if status >= 400:
        raise RuntimeError(f"GET {path} failed with {status}: {payload.decode(errors='ignore')}")
    return json.loads(payload.decode())


def _create_job(path: str, files: list[Path], fields: dict[str, str] | None = None) -> dict:
    payload, boundary = _multipart(fields or {}, [("files", file_path) for file_path in files])
    status, body = _request(
        "POST",
        path,
        data=payload,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    if status >= 400:
        raise RuntimeError(f"POST {path} failed with {status}: {body.decode(errors='ignore')}")
    return json.loads(body.decode())


def _wait_for_job(job_id: str) -> dict:
    deadline = time.time() + 90
    while time.time() < deadline:
        job = _json(f"/api/jobs/{job_id}")
        if job["status"] in {"completed", "failed"}:
            return job
        time.sleep(1.2)
    raise TimeoutError(f"Job {job_id} did not complete in time.")


def _download(file_id: str) -> bytes:
    status, payload = _request("GET", f"/downloads/{file_id}")
    if status >= 400:
        raise RuntimeError(f"Download {file_id} failed with {status}.")
    return payload


def _build_test_assets() -> dict[str, Path]:
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    image = TMP_DIR / "sample.png"
    with Image.new("RGB", (320, 220), "#f6f7fb") as canvas:
        draw = ImageDraw.Draw(canvas)
        draw.rounded_rectangle((30, 30, 290, 190), radius=28, fill="#0f766e")
        draw.ellipse((60, 55, 150, 145), fill="#f59e0b")
        draw.text((170, 85), "CreatorLab", fill="white")
        canvas.save(image, format="PNG")

    photo = TMP_DIR / "photo.jpg"
    with Image.new("RGB", (400, 260), "#ffffff") as canvas:
        draw = ImageDraw.Draw(canvas)
        draw.rectangle((100, 40, 300, 230), fill="#2563eb")
        draw.ellipse((140, 70, 260, 190), fill="#fde047")
        canvas.save(photo, format="JPEG", quality=95)

    image2 = TMP_DIR / "sample-2.jpg"
    with Image.new("RGB", (320, 240), "#fff7ed") as canvas:
        draw = ImageDraw.Draw(canvas)
        draw.rectangle((25, 30, 295, 210), fill="#7c3aed")
        draw.text((120, 105), "Page 2", fill="white")
        canvas.save(image2, format="JPEG", quality=94)

    pdf1 = TMP_DIR / "one.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=400, height=400)
    with pdf1.open("wb") as handle:
        writer.write(handle)

    pdf2 = TMP_DIR / "two.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=500, height=500)
    writer.add_blank_page(width=500, height=500)
    with pdf2.open("wb") as handle:
        writer.write(handle)

    split_pdf = TMP_DIR / "split-source.pdf"
    writer = PdfWriter()
    for _ in range(4):
        writer.add_blank_page(width=420, height=420)
    with split_pdf.open("wb") as handle:
        writer.write(handle)

    bad_file = TMP_DIR / "bad.txt"
    bad_file.write_text("not a supported upload", encoding="utf-8")

    bad_pdf = TMP_DIR / "bad.pdf"
    bad_pdf.write_bytes(b"not-a-real-pdf")

    return {
        "image": image,
        "photo": photo,
        "image2": image2,
        "pdf1": pdf1,
        "pdf2": pdf2,
        "split_pdf": split_pdf,
        "bad_file": bad_file,
        "bad_pdf": bad_pdf,
    }


def main() -> None:
    assets = _build_test_assets()

    health = _json("/health")
    if health["status"] != "ok":
        raise RuntimeError("Health check failed.")
    status, _ = _request("GET", "/health")
    if status != 200:
        raise RuntimeError("Health endpoint request failed.")

    results: list[str] = []

    compress_job = _create_job("/api/tools/compress/jobs", [assets["photo"]])
    compress_done = _wait_for_job(compress_job["id"])
    if not str(compress_done["outputs"][0]["share_url"]).startswith(BASE_URL):
        raise RuntimeError("Single-file download URLs must point to the backend origin.")
    compressed = _download(compress_done["outputs"][0]["file_id"])
    if len(compressed) >= assets["photo"].stat().st_size:
        raise RuntimeError("Compressed image is not smaller than the original JPEG.")
    results.append("compress")

    upscale_payload, upscale_boundary = _multipart({}, [("files", assets["image"])])
    status, body = _request(
        "POST",
        "/api/tools/upscale/jobs",
        data=upscale_payload,
        headers={"Content-Type": f"multipart/form-data; boundary={upscale_boundary}"},
    )
    if status != 503:
        raise RuntimeError(f"Upscale endpoint should be unavailable for now, but returned {status}: {body.decode(errors='ignore')}")
    results.append("upscale-coming-soon")

    remove_job = _create_job("/api/tools/background-remove/jobs", [assets["photo"]])
    remove_done = _wait_for_job(remove_job["id"])
    removed = Image.open(BytesIO(_download(remove_done["outputs"][0]["file_id"]))).convert("RGBA")
    if removed.getbbox() is None:
        raise RuntimeError("Background remover returned a fully empty image.")
    if removed.getpixel((0, 0))[3] != 0:
        raise RuntimeError("Background remover did not make the white border transparent.")
    results.append("background-remove")

    merge_job = _create_job("/api/tools/pdf/merge/jobs", [assets["pdf1"], assets["pdf2"]])
    merge_done = _wait_for_job(merge_job["id"])
    merged_reader = PdfReader(BytesIO(_download(merge_done["outputs"][0]["file_id"])))
    if len(merged_reader.pages) != 3:
        raise RuntimeError("Merged PDF page count is incorrect.")
    results.append("pdf-merge")

    split_job = _create_job("/api/tools/pdf/split/jobs", [assets["split_pdf"]], {"mode": "chunks", "chunk_size": "2"})
    split_done = _wait_for_job(split_job["id"])
    pdf_outputs = [item for item in split_done["outputs"] if item["content_type"] == "application/pdf"]
    zip_outputs = [item for item in split_done["outputs"] if item["content_type"] == "application/zip"]
    if len(pdf_outputs) != 2 or len(zip_outputs) != 1:
        raise RuntimeError("PDF chunk split did not produce the expected files and ZIP bundle.")
    if not str(zip_outputs[0]["share_url"]).startswith(BASE_URL):
        raise RuntimeError("ZIP download URL must point to the backend origin.")
    if split_done["meta"].get("download_all_url") != zip_outputs[0].get("share_url"):
        raise RuntimeError("PDF chunk split did not expose the ZIP download_all_url.")
    if pdf_outputs[0]["meta"].get("download_all_url") != zip_outputs[0].get("share_url"):
        raise RuntimeError("PDF chunk split did not attach the ZIP link to each output.")
    split_sizes = [len(PdfReader(BytesIO(_download(item["file_id"]))).pages) for item in pdf_outputs]
    if split_sizes != [2, 2]:
        raise RuntimeError(f"Unexpected split page counts: {split_sizes}")
    results.append("pdf-split")

    images_job = _create_job("/api/tools/pdf/images-to-pdf/jobs", [assets["image"], assets["image2"]])
    images_done = _wait_for_job(images_job["id"])
    image_pdf_reader = PdfReader(BytesIO(_download(images_done["outputs"][0]["file_id"])))
    if len(image_pdf_reader.pages) != 2:
        raise RuntimeError("Images-to-PDF output page count is incorrect.")
    results.append("images-to-pdf")

    invalid_payload, invalid_boundary = _multipart({}, [("files", assets["bad_file"])])
    status, body = _request(
        "POST",
        "/api/tools/compress/jobs",
        data=invalid_payload,
        headers={"Content-Type": f"multipart/form-data; boundary={invalid_boundary}"},
    )
    if status < 400:
        raise RuntimeError("Invalid upload should have failed but succeeded.")
    results.append("invalid-upload")

    bad_pdf_payload, bad_pdf_boundary = _multipart({"mode": "chunks", "chunk_size": "2"}, [("files", assets["bad_pdf"])])
    status, _ = _request(
        "POST",
        "/api/tools/pdf/split/jobs",
        data=bad_pdf_payload,
        headers={"Content-Type": f"multipart/form-data; boundary={bad_pdf_boundary}"},
    )
    if status < 400:
        raise RuntimeError("Malformed PDF upload should have failed but succeeded.")
    results.append("malformed-pdf")

    summary = _json("/api/admin/summary")
    if summary["completed_jobs"] < 6:
        raise RuntimeError("Admin summary did not include the completed smoke-test jobs.")
    if summary["processed_files"] < 7:
        raise RuntimeError("Admin summary file count looks incorrect after smoke tests.")
    if "runtime" not in summary:
        raise RuntimeError("Admin summary did not include runtime metadata.")
    results.append("admin-summary")

    history = _json("/api/jobs/history?page=1&page_size=5")
    if history["page"] != 1 or history["page_size"] != 5:
        raise RuntimeError("Paginated history response metadata is incorrect.")
    if not history["items"]:
        raise RuntimeError("Paginated history did not return any items.")
    results.append("job-history")

    print("Smoke tests passed:", ", ".join(results))


if __name__ == "__main__":
    main()
