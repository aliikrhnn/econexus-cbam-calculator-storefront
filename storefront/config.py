from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    secret_key: str
    base_url: str
    currency: str
    price_cents: int
    product_name: str
    product_tagline: str
    release_dir: Path
    mac_release_filename: str
    windows_release_filename: str
    download_file: Path
    download_url: str
    mac_download_url: str
    windows_download_url: str
    mac_secure_download_url: str
    windows_secure_download_url: str
    mac_download_note: str
    windows_download_note: str
    release_version: str
    token_ttl_hours: int
    download_limit: int
    payment_mode: str
    storage_mode: str
    stripe_secret_key: str
    stripe_publishable_key: str
    stripe_webhook_secret: str
    database_path: Path


def load_settings() -> Settings:
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    return Settings(
        secret_key=os.environ.get("SECRET_KEY", "dev-secret-key"),
        base_url=os.environ.get("STORE_BASE_URL", "http://127.0.0.1:8080").rstrip("/"),
        currency=os.environ.get("STORE_CURRENCY", "eur").lower(),
        price_cents=int(os.environ.get("STORE_PRICE_CENTS", "350000")),
        product_name=os.environ.get("STORE_PRODUCT_NAME", "Econexus Cbam Calculator"),
        product_tagline=os.environ.get(
            "STORE_PRODUCT_TAGLINE",
            "Desktop CBAM calculator for exporters",
        ),
        release_dir=Path(
            os.environ.get(
                "STORE_RELEASE_DIR",
                str(project_root / "releases"),
            )
        ).expanduser(),
        mac_release_filename=os.environ.get("STORE_MAC_RELEASE_FILENAME", "CBAM_Engine_Mac.zip").strip(),
        windows_release_filename=os.environ.get("STORE_WINDOWS_RELEASE_FILENAME", "CBAM_Engine_Windows.zip").strip(),
        download_file=Path(
            os.environ.get(
                "STORE_DOWNLOAD_FILE",
                "/Users/macbook/Documents/claudeiledenemeşeyler/cbam_tool/CBAM_Engine_Mac.zip",
            )
        ).expanduser(),
        download_url=os.environ.get("STORE_DOWNLOAD_URL", "").strip(),
        mac_download_url=os.environ.get("STORE_MAC_DOWNLOAD_URL", "").strip(),
        windows_download_url=os.environ.get("STORE_WINDOWS_DOWNLOAD_URL", "").strip(),
        mac_secure_download_url=os.environ.get("STORE_MAC_SECURE_DOWNLOAD_URL", "").strip(),
        windows_secure_download_url=os.environ.get("STORE_WINDOWS_SECURE_DOWNLOAD_URL", "").strip(),
        mac_download_note=os.environ.get(
            "STORE_MAC_DOWNLOAD_NOTE",
            "Recommended for macOS users. Delivered as a signed ZIP package when available.",
        ).strip(),
        windows_download_note=os.environ.get(
            "STORE_WINDOWS_DOWNLOAD_NOTE",
            "Recommended for Windows users. Download the packaged desktop build.",
        ).strip(),
        release_version=os.environ.get("STORE_RELEASE_VERSION", "Current release").strip(),
        token_ttl_hours=int(os.environ.get("STORE_TOKEN_TTL_HOURS", "72")),
        download_limit=int(os.environ.get("STORE_DOWNLOAD_LIMIT", "3")),
        payment_mode=os.environ.get("PAYMENT_MODE", "demo").lower(),
        storage_mode=os.environ.get("STORE_STORAGE_MODE", "database").lower(),
        stripe_secret_key=os.environ.get("STRIPE_SECRET_KEY", ""),
        stripe_publishable_key=os.environ.get("STRIPE_PUBLISHABLE_KEY", ""),
        stripe_webhook_secret=os.environ.get("STRIPE_WEBHOOK_SECRET", ""),
        database_path=data_dir / "storefront.sqlite3",
    )
