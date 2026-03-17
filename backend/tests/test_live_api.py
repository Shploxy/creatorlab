from __future__ import annotations

from io import BytesIO
import os
from pathlib import Path
import time
from urllib.parse import parse_qs, urlparse
import warnings
from uuid import uuid4

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import requests
from PIL import Image
from pypdf import PdfWriter


BASE_URL = os.environ.get("CREATORLAB_BASE_URL", "http://127.0.0.1:8000")
TMP_DIR = Path(__file__).resolve().parents[1] / "storage" / "pytest"


def _wait_for_job(job_id: str) -> dict:
    client = requests.Session()
    return _wait_for_job_with_client(client, job_id)


def _wait_for_job_with_client(client: requests.Session, job_id: str) -> dict:
    deadline = time.time() + 90
    while time.time() < deadline:
        response = client.get(f"{BASE_URL}/api/jobs/{job_id}", timeout=30)
        response.raise_for_status()
        payload = response.json()
        if payload["status"] in {"completed", "failed"}:
            return payload
        time.sleep(1)
    raise TimeoutError(f"Job {job_id} did not complete in time.")


def _build_assets() -> dict[str, Path]:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    image = TMP_DIR / "sample.png"
    Image.new("RGB", (120, 90), "#0f766e").save(image)

    photo = TMP_DIR / "photo.jpg"
    Image.new("RGB", (220, 180), "#ffffff").save(photo, quality=95)

    pdf = TMP_DIR / "sample.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=400, height=400)
    with pdf.open("wb") as handle:
        writer.write(handle)

    return {"image": image, "photo": photo, "pdf": pdf}


def _token_from_action_url(action_url: str) -> str:
    token = parse_qs(urlparse(action_url).query).get("token", [None])[0]
    if not token:
        raise AssertionError("No token found in action URL.")
    return token


def test_health_endpoint() -> None:
    response = requests.get(f"{BASE_URL}/health", timeout=30)
    response.raise_for_status()
    assert response.json()["status"] == "ok"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


def test_upscale_endpoint() -> None:
    assets = _build_assets()
    client = requests.Session()
    with assets["image"].open("rb") as file_obj:
        response = client.post(
            f"{BASE_URL}/api/tools/upscale/jobs",
            files={"files": ("sample.png", file_obj, "image/png")},
            timeout=60,
        )
    assert response.status_code == 503
    assert "coming soon" in response.text.lower()


def test_background_remove_endpoint() -> None:
    assets = _build_assets()
    client = requests.Session()
    with assets["photo"].open("rb") as file_obj:
        response = client.post(
            f"{BASE_URL}/api/tools/background-remove/jobs",
            files={"files": ("photo.jpg", file_obj, "image/jpeg")},
            timeout=60,
        )
    response.raise_for_status()
    payload = response.json()
    assert payload["tool"] == "background-remove"
    assert payload["status"] in {"queued", "processing"}


def test_compress_endpoint() -> None:
    assets = _build_assets()
    client = requests.Session()
    with assets["photo"].open("rb") as file_obj:
        response = client.post(
            f"{BASE_URL}/api/tools/compress/jobs",
            files={"files": ("photo.jpg", file_obj, "image/jpeg")},
            timeout=60,
        )
    response.raise_for_status()
    payload = response.json()
    assert payload["tool"] == "compress"
    assert payload["status"] in {"queued", "processing"}


def test_pdf_merge_endpoint() -> None:
    assets = _build_assets()
    client = requests.Session()
    with assets["pdf"].open("rb") as file_obj:
        response = client.post(
            f"{BASE_URL}/api/tools/pdf/merge/jobs",
            files=[("files", ("sample.pdf", file_obj, "application/pdf"))],
            timeout=60,
        )
    response.raise_for_status()
    payload = response.json()
    assert payload["tool"] == "pdf-merge"
    assert payload["status"] in {"queued", "processing"}


def test_pdf_split_chunks_endpoint() -> None:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    split_pdf = TMP_DIR / "chunk-source.pdf"
    writer = PdfWriter()
    for _ in range(5):
        writer.add_blank_page(width=400, height=400)
    with split_pdf.open("wb") as handle:
        writer.write(handle)

    client = requests.Session()
    with split_pdf.open("rb") as file_obj:
        response = client.post(
            f"{BASE_URL}/api/tools/pdf/split/jobs",
            files=[("files", ("chunk-source.pdf", file_obj, "application/pdf"))],
            data={"mode": "chunks", "chunk_size": "2"},
            timeout=60,
        )
    response.raise_for_status()
    payload = response.json()
    assert payload["tool"] == "pdf-split"
    assert payload["status"] in {"queued", "processing"}


def test_pdf_split_chunks_legacy_mode_still_accepted() -> None:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    split_pdf = TMP_DIR / "chunk-source-legacy.pdf"
    writer = PdfWriter()
    for _ in range(4):
        writer.add_blank_page(width=400, height=400)
    with split_pdf.open("wb") as handle:
        writer.write(handle)

    client = requests.Session()
    with split_pdf.open("rb") as file_obj:
        response = client.post(
            f"{BASE_URL}/api/tools/pdf/split/jobs",
            files=[("files", ("chunk-source-legacy.pdf", file_obj, "application/pdf"))],
            data={"split_mode": "split_chunks", "chunk_size": "0"},
            timeout=60,
        )
    response.raise_for_status()
    payload = response.json()
    assert payload["tool"] == "pdf-split"
    assert payload["status"] in {"queued", "processing"}


def test_invalid_upload_rejected() -> None:
    client = requests.Session()
    response = client.post(
        f"{BASE_URL}/api/tools/compress/jobs",
        files={"files": ("bad.txt", BytesIO(b"nope"), "text/plain")},
        timeout=60,
    )
    assert response.status_code >= 400


def test_malformed_pdf_rejected() -> None:
    client = requests.Session()
    response = client.post(
        f"{BASE_URL}/api/tools/pdf/split/jobs",
        files={"files": ("bad.pdf", BytesIO(b"not-a-real-pdf"), "application/pdf")},
        data={"mode": "chunks", "chunk_size": "2"},
        timeout=60,
    )
    assert response.status_code == 400


def test_auth_verification_reset_and_mine_history() -> None:
    assets = _build_assets()
    client = requests.Session()
    email = f"creatorlab-test-{uuid4().hex[:8]}@example.com"
    password = "Password123!"
    signup = client.post(
        f"{BASE_URL}/api/auth/signup",
        json={
            "email": email,
            "password": password,
            "full_name": "CreatorLab API Test",
        },
        timeout=30,
    )
    signup.raise_for_status()
    assert signup.json()["user"]["plan_key"] == "free"
    assert signup.json()["user"]["email_verified"] is False
    assert signup.json()["requires_email_verification"] is True

    me = client.get(f"{BASE_URL}/api/auth/me", timeout=30)
    me.raise_for_status()
    assert me.json()["user"]["email"] == email
    assert me.json()["user"]["email_verified"] is False

    verify_mail = client.get(
        f"{BASE_URL}/api/auth/dev/messages/latest",
        params={"email": email, "kind": "email_verification"},
        timeout=30,
    )
    verify_mail.raise_for_status()
    verify_token = _token_from_action_url(verify_mail.json()["action_url"])

    verify = client.post(f"{BASE_URL}/api/auth/verify-email", json={"token": verify_token}, timeout=30)
    verify.raise_for_status()

    me_verified = client.get(f"{BASE_URL}/api/auth/me", timeout=30)
    me_verified.raise_for_status()
    assert me_verified.json()["user"]["email_verified"] is True

    with assets["photo"].open("rb") as file_obj:
        response = client.post(
            f"{BASE_URL}/api/tools/compress/jobs",
            files={"files": ("photo.jpg", file_obj, "image/jpeg")},
            timeout=60,
        )
    response.raise_for_status()
    job = response.json()
    assert job["status"] in {"queued", "processing"}

    history = client.get(f"{BASE_URL}/api/jobs/history?mine=true&page=1&page_size=10", timeout=30)
    history.raise_for_status()
    payload = history.json()
    assert payload["total"] >= 1
    assert any(item["id"] == job["id"] for item in payload["items"])

    logout = client.post(f"{BASE_URL}/api/auth/logout", timeout=30)
    logout.raise_for_status()

    me_after = client.get(f"{BASE_URL}/api/auth/me", timeout=30)
    assert me_after.status_code == 401

    login = client.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password},
        timeout=30,
    )
    login.raise_for_status()

    forgot = client.post(f"{BASE_URL}/api/auth/forgot-password", json={"email": email}, timeout=30)
    forgot.raise_for_status()

    reset_mail = client.get(
        f"{BASE_URL}/api/auth/dev/messages/latest",
        params={"email": email, "kind": "password_reset"},
        timeout=30,
    )
    reset_mail.raise_for_status()
    reset_token = _token_from_action_url(reset_mail.json()["action_url"])

    reset = client.post(
        f"{BASE_URL}/api/auth/reset-password",
        json={"token": reset_token, "password": "Password456!"},
        timeout=30,
    )
    reset.raise_for_status()

    old_login = client.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password},
        timeout=30,
    )
    assert old_login.status_code == 401

    new_login = client.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": "Password456!"},
        timeout=30,
    )
    new_login.raise_for_status()


def test_anonymous_jobs_and_downloads_are_scoped_to_same_visitor() -> None:
    assets = _build_assets()
    owner = requests.Session()
    stranger = requests.Session()

    with assets["photo"].open("rb") as file_obj:
        create = owner.post(
            f"{BASE_URL}/api/tools/compress/jobs",
            files={"files": ("photo.jpg", file_obj, "image/jpeg")},
            timeout=60,
        )
    create.raise_for_status()
    owner.cookies.update(create.cookies)
    job = _wait_for_job_with_client(owner, create.json()["id"])
    assert job["status"] == "completed"

    download = owner.get(f"{BASE_URL}/downloads/{job['outputs'][0]['file_id']}", timeout=60)
    download.raise_for_status()
    assert download.headers["content-disposition"]

    blocked_job = stranger.get(f"{BASE_URL}/api/jobs/{job['id']}", timeout=30)
    assert blocked_job.status_code == 404

    blocked_download = stranger.get(f"{BASE_URL}/downloads/{job['outputs'][0]['file_id']}", timeout=30)
    assert blocked_download.status_code == 404
