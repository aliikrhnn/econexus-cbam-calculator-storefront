import os
import sys
from importlib import reload
from pathlib import Path

import storefront.config as storefront_config

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from storefront import app as storefront_app_module
from storefront.app import app, create_license_key, detect_platform


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


def test_release_download_serves_zip_only(monkeypatch):
    zip_path = Path(os.path.dirname(os.path.dirname(__file__))) / "releases" / "CBAM_Engine_Mac.zip"

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


def test_load_settings_skips_data_dir_creation_in_signed_mode(monkeypatch):
    mkdir_calls = []

    def fake_mkdir(self, parents=False, exist_ok=False):
        mkdir_calls.append((self, parents, exist_ok))

    monkeypatch.setenv("STORE_STORAGE_MODE", "signed")
    monkeypatch.setattr(Path, "mkdir", fake_mkdir)

    reload(storefront_config)
    settings = storefront_config.load_settings()

    assert settings.storage_mode == "signed"
    assert mkdir_calls == []


def test_load_settings_creates_data_dir_in_database_mode(monkeypatch):
    mkdir_calls = []

    def fake_mkdir(self, parents=False, exist_ok=False):
        mkdir_calls.append((self, parents, exist_ok))

    monkeypatch.setenv("STORE_STORAGE_MODE", "database")
    monkeypatch.setattr(Path, "mkdir", fake_mkdir)

    reload(storefront_config)
    settings = storefront_config.load_settings()

    assert settings.storage_mode == "database"
    assert len(mkdir_calls) == 1
    _, parents, exist_ok = mkdir_calls[0]
    assert parents is True
    assert exist_ok is True


def test_license_validation_endpoint_accepts_valid_license():
    license_key = create_license_key(checkout_ref="order-123", email="buyer@example.com")
    client = app.test_client()

    response = client.post(
        "/api/license/validate",
        json={
            "email": "buyer@example.com",
            "license_key": license_key,
            "device_id": "device-1",
        },
    )

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["valid"] is True
    assert payload["email"] == "buyer@example.com"
    assert payload["checkout_ref"] == "order-123"


def test_license_validation_endpoint_rejects_email_mismatch():
    license_key = create_license_key(checkout_ref="order-123", email="buyer@example.com")
    client = app.test_client()

    response = client.post(
        "/api/license/validate",
        json={
            "email": "other@example.com",
            "license_key": license_key,
            "device_id": "device-1",
        },
    )

    payload = response.get_json()
    assert response.status_code == 403
    assert payload["valid"] is False
    assert payload["error"] == "email_mismatch"
