import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from storefront import app as storefront_app_module
from storefront.app import app, detect_platform


def test_detect_platform_mac():
    assert detect_platform("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)") == "macOS"


def test_detect_platform_windows():
    assert detect_platform("Mozilla/5.0 (Windows NT 10.0; Win64; x64)") == "Windows"


def test_downloads_page_renders_platform_links():
    client = app.test_client()
    response = client.get("/downloads?lang=en")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Download for macOS" in html
    assert "Download for Windows" in html
    assert "CBAM_Engine_Mac.zip" in html
    assert "CBAM_Engine_Windows.zip" in html


def test_release_download_serves_zip_only(tmp_path, monkeypatch):
    zip_path = tmp_path / "CBAM_Engine_Mac.zip"
    zip_path.write_bytes(b"zip")

    monkeypatch.setattr(
        storefront_app_module,
        "resolve_release_target",
        lambda platform: (None, zip_path if platform == "mac" else None),
    )
    monkeypatch.setattr(
        storefront_app_module,
        "get_release_filename",
        lambda platform: "CBAM_Engine_Mac.zip",
    )

    client = app.test_client()
    response = client.get("/release/mac")

    assert response.status_code == 200
    assert "CBAM_Engine_Mac.zip" in response.headers.get("Content-Disposition", "")
    assert response.headers.get("Content-Type", "").startswith("application/zip")
