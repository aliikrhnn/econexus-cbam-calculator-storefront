from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

import stripe
from flask import Flask, abort, jsonify, redirect, render_template, request, send_file, url_for
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from storefront.config import load_settings
from storefront.db import StoreDB


settings = load_settings()
project_root = Path(__file__).resolve().parent.parent
app = Flask(
    __name__,
    template_folder=str(project_root / "templates"),
    static_folder=str(project_root / "public"),
    static_url_path="",
)
app.config["SECRET_KEY"] = settings.secret_key
app.logger.setLevel(logging.INFO)

db = None
if settings.storage_mode == "database":
    db = StoreDB(settings.database_path)
    db.init_db()

if settings.stripe_secret_key:
    stripe.api_key = settings.stripe_secret_key

download_serializer = URLSafeTimedSerializer(settings.secret_key, salt="cbam-storefront-download")
license_serializer = URLSafeTimedSerializer(settings.secret_key, salt="cbam-storefront-license")


SUPPORTED_LANGUAGES = ("tr", "en", "de")

COPY = {
    "tr": {
        "lang_code": "tr",
        "html_lang": "tr",
        "page_title": None,
        "eyebrow": "CBAM hesaplama aracı",
        "jump_link": "Lisans bölümüne git",
        "hero_badge": "Desktop License 2026",
        "lead": None,
        "sublead": (
            "CBAM yükümlülüğünü hızlı, izlenebilir ve raporlanabilir biçimde hesaplamak isteyen "
            "ihracat ekipleri, danışmanlar ve teknik operasyon birimleri için hazırlanmış masaüstü çözüm."
        ),
        "hero_point_1_title": "Türkçe + İngilizce",
        "hero_point_1_text": "Çok dilli kullanım ve sonuç akışı",
        "hero_point_2_title": "XLSX çıktısı",
        "hero_point_2_text": "Hazır rapor ve çalışma çıktısı üretimi",
        "hero_point_3_title": "Çok ürünlü kurgu",
        "hero_point_3_text": "Allocation, precursor ve ürün bazlı özetler",
        "license_tag": "Yıllık lisans",
        "price_note": "KDV hariç / yıllık kullanım hakkı",
        "delivery_title": "Teslim modeli",
        "delivery_text": "Ödeme sonrası anında indirme",
        "usage_title": "Kullanım tipi",
        "usage_text": "Masaüstü uygulama",
        "email_label": "Satın alma e-postası",
        "email_placeholder": "ornek@sirket.com",
        "buy_button": "Lisansı Satın Al",
        "trust_1": "CBAM hesapları",
        "trust_2": "Ürün bazlı çıktı",
        "trust_3": "Excel raporu",
        "download_missing": "İndirme bağlantısı henüz eklenmedi. Platform bazlı release dosyası veya URL ayarlarını yapılandırın.",
        "metric_1_label": "Hesap kapsamı",
        "metric_1_title": "Direct + Indirect",
        "metric_1_text": "Gömülü emisyonların ana CBAM kalemleri tek akışta hesaplanır.",
        "metric_2_label": "Operasyon akışı",
        "metric_2_title": "Allocation Ready",
        "metric_2_text": "Çok ürünlü dağıtım ve ürün bazlı net sonuç ekranı hazır gelir.",
        "metric_3_label": "Çıktı formatı",
        "metric_3_title": "XLSX Export",
        "metric_3_text": "Sonuçlar masaüstünden dışa aktarılıp paylaşılabilir.",
        "workflow_kicker": "Kullanım akışı",
        "workflow_title": "Nasıl çalışır",
        "workflow_1_title": "Veriyi gir",
        "workflow_1_text": "Üretim miktarı, enerji, precursor ve karbon fiyatı verilerini tek ekranda gir.",
        "workflow_2_title": "CBAM sonucunu gör",
        "workflow_2_text": "Direkt, dolaylı, toplam embedded emissions ve net CBAM yükümlülüğü anında oluşur.",
        "workflow_3_title": "Kaydet ve dışa aktar",
        "workflow_3_text": "Hesapları kaydet, yeniden yükle ve XLSX çıktısı ile ekip içinde dağıt.",
        "features_kicker": "Ürün kabiliyetleri",
        "features_title": "Uygulama özellikleri",
        "feature_1_title": "CBAM hesap çekirdeği",
        "feature_1_text": "Direkt, dolaylı ve toplam gömülü emisyonlar ile net CBAM yükümlülüğü aynı akışta üretilir.",
        "feature_2_title": "Çok ürünlü allocation",
        "feature_2_text": "Ürün bazlı allocation, summary table ve route-specific sonuç görünümü.",
        "feature_3_title": "Precursor desteği",
        "feature_3_text": "Purchased precursor girdileri, SEE direct / indirect ve ürün eşleme desteği.",
        "feature_4_title": "Enerji detayları",
        "feature_4_text": "Specific intensities, fuel streams ve electricity EF seçenekleri birlikte çalışır.",
        "feature_5_title": "Kayıt ve tekrar kullanım",
        "feature_5_text": "Kaydedilmiş hesaplar ile tekrar açma ve iş akışı sürekliliği.",
        "feature_6_title": "Excel deliverable",
        "feature_6_text": "XLSX export ile sonuçlar, girdiler ve özet tablolar operasyon kullanımına hazır hale gelir.",
        "spotlight_kicker": "Önerilen kullanım",
        "spotlight_title": "Satış sürecini daha net yapan üç avantaj",
        "spotlight_1_title": "İç ekipler için hızlı onboarding",
        "spotlight_1_text": "Terminal, kurulum karmaşası veya eğitim yükü olmadan doğrudan masaüstü kullanım.",
        "spotlight_2_title": "Danışmanlık çıktısına uygun teslim",
        "spotlight_2_text": "Kaydedilmiş hesaplar ve XLSX çıktısı ile müşteri ya da ekip paylaşımı kolaylaşır.",
        "spotlight_3_title": "Operasyonel tekrar kullanıma uygun",
        "spotlight_3_text": "Aynı akış, yeni veri setleriyle tekrar çalıştırılıp düzenli raporlama için kullanılabilir.",
        "success_title": "İndirme Hazır",
        "success_eyebrow": "Ödeme tamamlandı",
        "success_lead": "İndirmeniz hazır.",
        "success_sublead": "Süre bitimi: {expires_at}",
        "download_button": "Uygulamayı İndir",
        "success_note": "Link sınırlı kullanım sayısına sahiptir. Kurulum dosyasını güvenli bir yerde saklayın.",
        "downloads_nav": "İndirme sayfası",
        "downloads_title": "Masaüstü sürümünü indir",
        "downloads_sublead": "İşletim sisteminize uygun paketi seçin. Yanlış dosya indirme riskini azaltmak için macOS ve Windows sürümleri ayrı sunulur.",
        "downloads_hint": "Algılanan cihaz",
        "downloads_hint_none": "Algılanamadı",
        "downloads_version_label": "Release",
        "downloads_mac_title": "macOS İndir",
        "downloads_windows_title": "Windows İndir",
        "downloads_mac_button": "macOS için indir",
        "downloads_windows_button": "Windows için indir",
        "downloads_missing": "İndirme linki henüz eklenmedi. Deploy ortamında ilgili URL ayarını güncelleyin.",
        "downloads_notes_title": "Kısa notlar",
        "downloads_note_1": "Dosya adları platform bazlı ayrılmıştır: CBAM_Engine_Mac.zip ve CBAM_Engine_Windows.zip.",
        "downloads_note_2": "Yeni release geldiğinde sadece ortam değişkenlerindeki linkleri güncellemeniz yeterlidir.",
        "downloads_note_3": "Otomatik yönlendirme yapılmaz; kullanıcı doğru paketi açıkça seçer.",
    },
    "en": {
        "lang_code": "en",
        "html_lang": "en",
        "page_title": None,
        "eyebrow": "CBAM calculation tool",
        "jump_link": "Go to licensing",
        "hero_badge": "Desktop License 2026",
        "lead": None,
        "sublead": (
            "A desktop solution built for exporters, consultants, and technical operations teams "
            "that need fast, traceable, and report-ready CBAM liability calculations."
        ),
        "hero_point_1_title": "Turkish + English",
        "hero_point_1_text": "Multilingual workflow and output experience",
        "hero_point_2_title": "XLSX export",
        "hero_point_2_text": "Ready-to-share reporting output from the desktop app",
        "hero_point_3_title": "Multi-product setup",
        "hero_point_3_text": "Allocation, precursor support, and product-level summaries",
        "license_tag": "Annual license",
        "price_note": "Excluding VAT / annual usage right",
        "delivery_title": "Delivery model",
        "delivery_text": "Instant download after payment",
        "usage_title": "Usage type",
        "usage_text": "Desktop application",
        "email_label": "Purchase email",
        "email_placeholder": "name@company.com",
        "buy_button": "Buy the License",
        "trust_1": "CBAM calculations",
        "trust_2": "Product-level output",
        "trust_3": "Excel report",
        "download_missing": "The download target is not configured yet. Set the platform release file or URL values first.",
        "metric_1_label": "Calculation scope",
        "metric_1_title": "Direct + Indirect",
        "metric_1_text": "Core CBAM embedded-emissions items are calculated in one flow.",
        "metric_2_label": "Operational flow",
        "metric_2_title": "Allocation Ready",
        "metric_2_text": "Built for multi-product allocation and product-level net results.",
        "metric_3_label": "Output format",
        "metric_3_title": "XLSX Export",
        "metric_3_text": "Results can be exported and shared from the desktop app.",
        "workflow_kicker": "Workflow",
        "workflow_title": "How it works",
        "workflow_1_title": "Enter the data",
        "workflow_1_text": "Input production, energy, precursor, and carbon-price data in one screen.",
        "workflow_2_title": "Review the CBAM result",
        "workflow_2_text": "Direct, indirect, total embedded emissions, and net CBAM liability are produced instantly.",
        "workflow_3_title": "Save and export",
        "workflow_3_text": "Save calculations, reopen them later, and distribute XLSX outputs across the team.",
        "features_kicker": "Product capabilities",
        "features_title": "Application features",
        "feature_1_title": "CBAM calculation core",
        "feature_1_text": "Direct, indirect, total embedded emissions, and net CBAM liability are generated in one calculation flow.",
        "feature_2_title": "Multi-product allocation",
        "feature_2_text": "Product-level allocation, summary tables, and route-specific result views.",
        "feature_3_title": "Precursor support",
        "feature_3_text": "Purchased precursor inputs, SEE direct/indirect values, and product mapping support.",
        "feature_4_title": "Energy details",
        "feature_4_text": "Specific intensities, fuel streams, and electricity EF options work together.",
        "feature_5_title": "Save and reuse",
        "feature_5_text": "Saved calculations support repeat workflows and consistent reporting.",
        "feature_6_title": "Excel deliverable",
        "feature_6_text": "XLSX exports make results, inputs, and summary tables ready for operational use.",
        "spotlight_kicker": "Suggested positioning",
        "spotlight_title": "Three advantages that strengthen the sales page",
        "spotlight_1_title": "Fast onboarding for internal teams",
        "spotlight_1_text": "Desktop-first usage without terminal friction, setup confusion, or training-heavy rollout.",
        "spotlight_2_title": "Deliverable-ready for consulting work",
        "spotlight_2_text": "Saved calculations and XLSX output make client and team handoff much easier.",
        "spotlight_3_title": "Built for repeated operational use",
        "spotlight_3_text": "Run the same flow again with new data sets for recurring reporting cycles.",
        "success_title": "Download Ready",
        "success_eyebrow": "Payment completed",
        "success_lead": "Your download is ready.",
        "success_sublead": "Expiration: {expires_at}",
        "download_button": "Download the App",
        "success_note": "The link has a limited number of uses. Keep the installer file in a safe location.",
        "downloads_nav": "Download page",
        "downloads_title": "Download the desktop build",
        "downloads_sublead": "Choose the package that matches your operating system. macOS and Windows builds are separated clearly to reduce download mistakes.",
        "downloads_hint": "Detected device",
        "downloads_hint_none": "Not detected",
        "downloads_version_label": "Release",
        "downloads_mac_title": "Download for macOS",
        "downloads_windows_title": "Download for Windows",
        "downloads_mac_button": "Download for macOS",
        "downloads_windows_button": "Download for Windows",
        "downloads_missing": "The download link is not configured yet. Update the matching deployment URL setting.",
        "downloads_notes_title": "Release notes",
        "downloads_note_1": "Artifact names stay platform-specific: CBAM_Engine_Mac.zip and CBAM_Engine_Windows.zip.",
        "downloads_note_2": "When a new release is ready, only the configured URLs need to be updated.",
        "downloads_note_3": "No forced redirect is used; the user explicitly chooses the correct package.",
    },
    "de": {
        "lang_code": "de",
        "html_lang": "de",
        "page_title": None,
        "eyebrow": "CBAM-Berechnungstool",
        "jump_link": "Zum Lizenzbereich",
        "hero_badge": "Desktop-Lizenz 2026",
        "lead": None,
        "sublead": (
            "Eine Desktop-Lösung für Exporteure, Berater und technische Teams, "
            "die CBAM-Verpflichtungen schnell, nachvollziehbar und berichtsfähig berechnen müssen."
        ),
        "hero_point_1_title": "Türkisch + Englisch",
        "hero_point_1_text": "Mehrsprachiger Ablauf und Ausgabe",
        "hero_point_2_title": "XLSX-Export",
        "hero_point_2_text": "Desktop-Ausgabe für Berichte und operative Weitergabe",
        "hero_point_3_title": "Mehrprodukt-Struktur",
        "hero_point_3_text": "Allocation, Precursor-Support und produktbezogene Zusammenfassungen",
        "license_tag": "Jahreslizenz",
        "price_note": "Zzgl. MwSt. / jährliches Nutzungsrecht",
        "delivery_title": "Bereitstellung",
        "delivery_text": "Sofortiger Download nach der Zahlung",
        "usage_title": "Nutzungstyp",
        "usage_text": "Desktop-Anwendung",
        "email_label": "E-Mail für den Kauf",
        "email_placeholder": "name@unternehmen.de",
        "buy_button": "Lizenz kaufen",
        "trust_1": "CBAM-Berechnungen",
        "trust_2": "Produktbezogene Ausgabe",
        "trust_3": "Excel-Bericht",
        "download_missing": "Das Download-Ziel ist noch nicht konfiguriert. Legen Sie zuerst die plattformspezifischen Release-Dateien oder URLs fest.",
        "metric_1_label": "Berechnungsumfang",
        "metric_1_title": "Direkt + Indirekt",
        "metric_1_text": "Die zentralen CBAM-Positionen für eingebettete Emissionen werden in einem Ablauf berechnet.",
        "metric_2_label": "Betriebsablauf",
        "metric_2_title": "Allocation Ready",
        "metric_2_text": "Für Multi-Produkt-Allocation und produktbezogene Nettoergebnisse vorbereitet.",
        "metric_3_label": "Ausgabeformat",
        "metric_3_title": "XLSX-Export",
        "metric_3_text": "Ergebnisse können aus der Desktop-App exportiert und geteilt werden.",
        "workflow_kicker": "Ablauf",
        "workflow_title": "So funktioniert es",
        "workflow_1_title": "Daten eingeben",
        "workflow_1_text": "Produktions-, Energie-, Precursor- und CO2-Preisdaten in einer Oberfläche erfassen.",
        "workflow_2_title": "CBAM-Ergebnis prüfen",
        "workflow_2_text": "Direkte, indirekte und gesamte eingebettete Emissionen sowie die Netto-CBAM-Verpflichtung werden sofort berechnet.",
        "workflow_3_title": "Speichern und exportieren",
        "workflow_3_text": "Berechnungen speichern, später erneut öffnen und XLSX-Ausgaben im Team verteilen.",
        "features_kicker": "Produktfunktionen",
        "features_title": "Anwendungsfunktionen",
        "feature_1_title": "CBAM-Berechnungskern",
        "feature_1_text": "Direkte, indirekte und gesamte eingebettete Emissionen sowie die Netto-CBAM-Verpflichtung entstehen in einem Ablauf.",
        "feature_2_title": "Multi-Produkt-Allocation",
        "feature_2_text": "Produktbezogene Allocation, Summary-Tabellen und route-spezifische Ergebnisansichten.",
        "feature_3_title": "Precursor-Unterstützung",
        "feature_3_text": "Purchased-Precursor-Eingaben, SEE direct/indirect-Werte und Produktzuordnung.",
        "feature_4_title": "Energiedetails",
        "feature_4_text": "Specific Intensities, Fuel Streams und Electricity-EF-Optionen arbeiten zusammen.",
        "feature_5_title": "Speichern und wiederverwenden",
        "feature_5_text": "Gespeicherte Berechnungen unterstützen wiederkehrende Abläufe und konsistentes Reporting.",
        "feature_6_title": "Excel-Deliverable",
        "feature_6_text": "XLSX-Exporte machen Ergebnisse, Eingaben und Summary-Tabellen sofort operativ nutzbar.",
        "spotlight_kicker": "Empfohlene Positionierung",
        "spotlight_title": "Drei Vorteile für eine stärkere Verkaufsseite",
        "spotlight_1_title": "Schnelles Onboarding für interne Teams",
        "spotlight_1_text": "Desktop-first Nutzung ohne Terminal-Hürden, Setup-Verwirrung oder hohen Schulungsaufwand.",
        "spotlight_2_title": "Geeignet für Beratungs-Deliverables",
        "spotlight_2_text": "Gespeicherte Berechnungen und XLSX-Ausgaben erleichtern die Übergabe an Kunden und Teams.",
        "spotlight_3_title": "Für wiederholte operative Nutzung gebaut",
        "spotlight_3_text": "Der gleiche Ablauf kann mit neuen Datensätzen für regelmäßige Reporting-Zyklen erneut genutzt werden.",
        "success_title": "Download bereit",
        "success_eyebrow": "Zahlung abgeschlossen",
        "success_lead": "Ihr Download ist bereit.",
        "success_sublead": "Ablaufzeit: {expires_at}",
        "download_button": "App herunterladen",
        "success_note": "Der Link hat eine begrenzte Anzahl an Nutzungen. Bewahren Sie die Installationsdatei sicher auf.",
        "downloads_nav": "Download-Seite",
        "downloads_title": "Desktop-Version herunterladen",
        "downloads_sublead": "Wählen Sie das Paket passend zu Ihrem Betriebssystem. macOS- und Windows-Builds sind klar getrennt, damit keine falsche Datei geladen wird.",
        "downloads_hint": "Erkanntes Gerät",
        "downloads_hint_none": "Nicht erkannt",
        "downloads_version_label": "Release",
        "downloads_mac_title": "Für macOS herunterladen",
        "downloads_windows_title": "Für Windows herunterladen",
        "downloads_mac_button": "Für macOS herunterladen",
        "downloads_windows_button": "Für Windows herunterladen",
        "downloads_missing": "Der Download-Link ist noch nicht konfiguriert. Aktualisieren Sie die passende URL in den Deployment-Einstellungen.",
        "downloads_notes_title": "Kurznotizen",
        "downloads_note_1": "Die Dateinamen bleiben plattformspezifisch: CBAM_Engine_Mac.zip und CBAM_Engine_Windows.zip.",
        "downloads_note_2": "Für ein neues Release müssen später nur die hinterlegten URLs aktualisiert werden.",
        "downloads_note_3": "Es gibt keine erzwungene Weiterleitung; der Nutzer wählt das richtige Paket selbst.",
    },
}


def price_display() -> str:
    return f"{settings.price_cents / 100:,.0f} EUR".replace(",", ".")


def is_download_available() -> bool:
    if settings.payment_mode == "lemonsqueezy":
        return True
    return bool(resolve_release_target("mac")[0] or resolve_release_target("mac")[1]) or bool(
        resolve_release_target("windows")[0] or resolve_release_target("windows")[1]
    )


def is_stateless_mode() -> bool:
    return settings.storage_mode == "signed"


def ensure_db() -> StoreDB:
    if db is None:
        raise RuntimeError("Database mode is not active.")
    return db


def create_signed_download_token(*, checkout_ref: str, email: str, payment_mode: str) -> str:
    return download_serializer.dumps(
        {
            "checkout_ref": checkout_ref,
            "email": email,
            "payment_mode": payment_mode,
        }
    )


def load_signed_download_token(token: str) -> dict[str, str]:
    return download_serializer.loads(token, max_age=settings.token_ttl_hours * 3600)


def create_license_key(*, checkout_ref: str, email: str) -> str:
    issued_at = datetime.now(UTC).replace(microsecond=0)
    expires_at = datetime.fromtimestamp(
        issued_at.timestamp() + settings.license_duration_days * 86400,
        tz=UTC,
    )
    return license_serializer.dumps(
        {
            "checkout_ref": checkout_ref,
            "email": email.strip().lower(),
            "issued_at": issued_at.isoformat(),
            "expires_at": expires_at.isoformat(),
        }
    )


def load_license_key(license_key: str) -> dict[str, str]:
    return license_serializer.loads(license_key)


def validate_license_key(*, email: str, license_key: str) -> tuple[bool, dict[str, str] | None, str | None]:
    try:
        payload = load_license_key(license_key.strip())
    except BadSignature:
        return False, None, "invalid_license"

    normalized_email = email.strip().lower()
    if payload.get("email", "").strip().lower() != normalized_email:
        return False, None, "email_mismatch"

    expires_at = payload.get("expires_at", "")
    try:
        expires_at_value = datetime.fromisoformat(expires_at)
    except ValueError:
        return False, None, "invalid_license"

    if expires_at_value < datetime.now(UTC):
        return False, payload, "license_expired"

    return True, payload, None


def create_lemonsqueezy_checkout(*, email: str, lang: str) -> str:
    if not settings.lemon_squeezy_api_key or not settings.lemon_squeezy_store_id or not settings.lemon_squeezy_variant_id:
        raise RuntimeError("Lemon Squeezy is not configured.")

    payload = {
        "data": {
            "type": "checkouts",
            "attributes": {
                "checkout_data": {
                    "email": email,
                    "custom": {
                        "source": "econexus-cbam-storefront",
                    },
                },
                "checkout_options": {
                    "embed": False,
                    "media": True,
                    "logo": True,
                    "desc": True,
                    "discount": True,
                    "subscription_preview": False,
                    "button_color": "#163b70",
                    "checkout_button_color": "#163b70",
                    "dark": False,
                    "language": lang,
                },
                "product_options": {
                    "enabled_variants": [int(settings.lemon_squeezy_variant_id)],
                    "redirect_url": f"{settings.base_url}{url_for('checkout_success', lang=lang)}",
                    "receipt_button_text": "Open download instructions",
                    "receipt_link_url": f"{settings.base_url}{url_for('checkout_success', lang=lang)}",
                    "receipt_thank_you_note": "Keep your Lemon Squeezy license key and purchase email for desktop activation.",
                },
            },
            "relationships": {
                "store": {"data": {"type": "stores", "id": settings.lemon_squeezy_store_id}},
                "variant": {"data": {"type": "variants", "id": settings.lemon_squeezy_variant_id}},
            },
        }
    }

    req = Request(
        "https://api.lemonsqueezy.com/v1/checkouts",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {settings.lemon_squeezy_api_key}",
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
        },
    )

    try:
        with urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        app.logger.error("Lemon Squeezy checkout creation failed: %s", body)
        raise RuntimeError("Lemon Squeezy checkout failed.") from exc
    except URLError as exc:
        raise RuntimeError("Lemon Squeezy checkout failed.") from exc

    checkout_url = data.get("data", {}).get("attributes", {}).get("url", "").strip()
    if not checkout_url:
        raise RuntimeError("Lemon Squeezy checkout URL missing.")
    return checkout_url


def get_lang() -> str:
    lang = request.values.get("lang", request.args.get("lang", "tr")).strip().lower()
    return lang if lang in SUPPORTED_LANGUAGES else "tr"


def get_copy(lang: str) -> dict[str, str]:
    data = dict(COPY[lang])
    data["page_title"] = settings.product_name
    data["lead"] = settings.product_tagline
    return data


def detect_platform(user_agent: str) -> str | None:
    ua = user_agent.lower()
    if "mac os x" in ua or "macintosh" in ua:
        return "macOS"
    if "windows" in ua or "win64" in ua or "win32" in ua:
        return "Windows"
    return None


def normalize_platform(platform: str | None) -> str:
    value = (platform or "").strip().lower()
    if value in {"mac", "macos", "darwin"}:
        return "mac"
    if value in {"windows", "win", "win32", "win64"}:
        return "windows"
    abort(404)


def is_zip_path(path: Path | None) -> bool:
    return path is not None and path.suffix.lower() == ".zip"


def is_zip_url(url: str | None) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    return parsed.path.lower().endswith(".zip")


def resolve_release_target(platform: str) -> tuple[str | None, Path | None]:
    normalized = normalize_platform(platform)
    if normalized == "mac":
        external_url = settings.mac_download_url if is_zip_url(settings.mac_download_url) else None
        file_path = settings.release_dir / settings.mac_release_filename
        return external_url, file_path if file_path.is_file() and is_zip_path(file_path) else None

    external_url = settings.windows_download_url if is_zip_url(settings.windows_download_url) else None
    file_path = settings.release_dir / settings.windows_release_filename
    return external_url, file_path if file_path.is_file() and is_zip_path(file_path) else None


def get_release_filename(platform: str) -> str:
    normalized = normalize_platform(platform)
    return settings.mac_release_filename if normalized == "mac" else settings.windows_release_filename


def resolve_platform_download_urls(*, access_token: str | None = None) -> tuple[str, str]:
    if access_token:
        mac_url = (
            settings.mac_secure_download_url
            if is_zip_url(settings.mac_secure_download_url)
            else f"{settings.base_url}{url_for('download', token=access_token, platform='mac')}"
        )
        windows_url = (
            settings.windows_secure_download_url
            if is_zip_url(settings.windows_secure_download_url)
            else f"{settings.base_url}{url_for('download', token=access_token, platform='windows')}"
        )
        return mac_url, windows_url

    mac_external, mac_file = resolve_release_target("mac")
    windows_external, windows_file = resolve_release_target("windows")

    mac_url = mac_external or (f"{settings.base_url}{url_for('release_download', platform='mac')}" if mac_file else "")
    windows_url = windows_external or (
        f"{settings.base_url}{url_for('release_download', platform='windows')}" if windows_file else ""
    )
    return mac_url, windows_url


@app.get("/")
def index():
    lang = get_lang()
    return render_template(
        "index.html",
        product_name=settings.product_name,
        product_tagline=settings.product_tagline,
        price_display=price_display(),
        stripe_enabled=settings.payment_mode == "stripe",
        stripe_publishable_key=settings.stripe_publishable_key,
        download_available=is_download_available(),
        current_lang=lang,
        copy=get_copy(lang),
    )


@app.get("/downloads")
def downloads():
    lang = get_lang()
    detected_platform = detect_platform(request.headers.get("User-Agent", ""))
    mac_download_url, windows_download_url = resolve_platform_download_urls()
    return render_template(
        "downloads.html",
        product_name=settings.product_name,
        product_tagline=settings.product_tagline,
        current_lang=lang,
        copy=get_copy(lang),
        detected_platform=detected_platform,
        mac_download_url=mac_download_url,
        windows_download_url=windows_download_url,
        mac_download_note=settings.mac_download_note,
        windows_download_note=settings.windows_download_note,
        release_version=settings.release_version,
        access_email="",
        access_reference="",
        expires_at=None,
        secure_access=False,
    )


@app.get("/release/<platform>")
def release_download(platform: str):
    external_url, file_path = resolve_release_target(platform)
    if external_url:
        return redirect(external_url, code=302)
    if file_path is None:
        abort(404, "Release artifact missing.")
    return send_file(
        file_path,
        as_attachment=True,
        download_name=get_release_filename(platform),
        mimetype="application/zip",
        max_age=0,
    )


@app.post("/checkout")
def checkout():
    lang = get_lang()
    email = request.form.get("email", "").strip()
    if not email:
        abort(400, "Email is required.")

    if not is_download_available():
        abort(500, "Download target is not configured.")

    if settings.payment_mode == "demo":
        checkout_ref = f"demo_{datetime.now(UTC).timestamp()}"
        if is_stateless_mode():
            app.logger.info("Created stateless demo order %s for %s", checkout_ref, email)
        else:
            ensure_db().mark_paid(
                checkout_ref=checkout_ref,
                email=email,
                payment_mode="demo",
                token_ttl_hours=settings.token_ttl_hours,
                download_limit=settings.download_limit,
            )
        app.logger.info("Created demo paid order %s for %s", checkout_ref, email)
        return redirect(url_for("checkout_success", session_id=checkout_ref, lang=lang, email=email))

    if settings.payment_mode == "lemonsqueezy":
        checkout_url = create_lemonsqueezy_checkout(email=email, lang=lang)
        app.logger.info("Created Lemon Squeezy checkout for %s", email)
        return redirect(checkout_url, code=303)

    if settings.payment_mode != "stripe" or not settings.stripe_secret_key:
        abort(500, "Stripe is not configured.")

    session = stripe.checkout.Session.create(
        mode="payment",
        customer_email=email,
        success_url=f"{settings.base_url}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}&lang={lang}",
        cancel_url=f"{settings.base_url}/?lang={lang}#pricing",
        line_items=[
            {
                "price_data": {
                    "currency": settings.currency,
                    "product_data": {
                        "name": settings.product_name,
                        "description": settings.product_tagline,
                    },
                    "unit_amount": settings.price_cents,
                },
                "quantity": 1,
            }
        ],
    )
    app.logger.info("Created Stripe checkout session %s for %s", session.id, email)
    return redirect(session.url, code=303)


@app.get("/checkout/success")
def checkout_success():
    lang = get_lang()
    if settings.payment_mode == "lemonsqueezy":
        return render_template(
            "downloads.html",
            product_name=settings.product_name,
            current_lang=lang,
            copy=get_copy(lang),
            detected_platform=detect_platform(request.headers.get("User-Agent", "")),
            mac_download_url="",
            windows_download_url="",
            mac_download_note="Access your downloads from the Lemon Squeezy receipt or My Orders page.",
            windows_download_note="Use the license key from Lemon Squeezy to activate the desktop app after download.",
            release_version=settings.release_version,
            access_email="",
            access_reference="",
            expires_at=None,
            license_key="Check your Lemon Squeezy order receipt",
            license_expires_at=None,
            secure_access=True,
        )

    session_id = request.args.get("session_id", "").strip()
    if not session_id:
        abort(400, "Missing session id.")

    if settings.payment_mode == "demo":
        if is_stateless_mode():
            email = request.args.get("email", "").strip()
            if not email:
                email = "customer"
            order = {
                "email": email,
                "checkout_ref": session_id,
                "payment_mode": "demo",
            }
        else:
            order = ensure_db().get_order_by_checkout_ref(session_id)
            if not order:
                abort(404, "Order not found.")
    else:
        if not settings.stripe_secret_key:
            abort(500, "Stripe is not configured.")
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status != "paid":
            abort(403, "Payment not completed.")
        email = session.customer_details.email or session.customer_email or ""
        if is_stateless_mode():
            order = {
                "email": email,
                "checkout_ref": session.id,
                "payment_mode": "stripe",
            }
        else:
            order = ensure_db().mark_paid(
                checkout_ref=session.id,
                email=email,
                payment_mode="stripe",
                token_ttl_hours=settings.token_ttl_hours,
                download_limit=settings.download_limit,
            )
            app.logger.info("Marked Stripe order %s as paid", session.id)

    if is_stateless_mode():
        token = create_signed_download_token(
            checkout_ref=order["checkout_ref"],
            email=order["email"],
            payment_mode=order["payment_mode"],
        )
        expires_at = datetime.now(UTC).replace(microsecond=0)
        expires_at = datetime.fromtimestamp(expires_at.timestamp() + settings.token_ttl_hours * 3600, tz=UTC)
        access_token = token
    else:
        access_token = order["token"]
        expires_at = datetime.fromisoformat(order["token_expires_at"])

    license_key = create_license_key(
        checkout_ref=order["checkout_ref"],
        email=order["email"],
    )
    license_payload = load_license_key(license_key)
    mac_download_url, windows_download_url = resolve_platform_download_urls(access_token=access_token)
    detected_platform = detect_platform(request.headers.get("User-Agent", ""))

    return render_template(
        "downloads.html",
        product_name=settings.product_name,
        current_lang=lang,
        copy=get_copy(lang),
        detected_platform=detected_platform,
        mac_download_url=mac_download_url,
        windows_download_url=windows_download_url,
        mac_download_note=settings.mac_download_note,
        windows_download_note=settings.windows_download_note,
        release_version=settings.release_version,
        access_email=order["email"],
        access_reference=order["checkout_ref"],
        expires_at=expires_at,
        license_key=license_key,
        license_expires_at=datetime.fromisoformat(license_payload["expires_at"]),
        secure_access=True,
    )


@app.post("/api/license/validate")
def validate_license():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email", "")).strip()
    license_key = str(payload.get("license_key", "")).strip()
    device_id = str(payload.get("device_id", "")).strip()

    if not email or not license_key:
        return jsonify({"valid": False, "error": "missing_credentials"}), 400
    if not device_id:
        return jsonify({"valid": False, "error": "missing_device_id"}), 400

    is_valid, license_payload, error = validate_license_key(email=email, license_key=license_key)
    if not is_valid or license_payload is None:
        status_code = 403 if error in {"email_mismatch", "license_expired"} else 400
        return jsonify({"valid": False, "error": error}), status_code

    return jsonify(
        {
            "valid": True,
            "email": license_payload["email"],
            "checkout_ref": license_payload["checkout_ref"],
            "expires_at": license_payload["expires_at"],
            "issued_at": license_payload["issued_at"],
            "device_id": device_id,
        }
    )


@app.post("/webhooks/stripe")
def stripe_webhook():
    if not settings.stripe_webhook_secret:
        abort(404)

    payload = request.get_data(as_text=True)
    signature = request.headers.get("Stripe-Signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            signature,
            settings.stripe_webhook_secret,
        )
    except Exception:
        app.logger.exception("Invalid Stripe webhook")
        abort(400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        if session.get("payment_status") == "paid" and not is_stateless_mode():
            order = ensure_db().mark_paid(
                checkout_ref=session["id"],
                email=session.get("customer_details", {}).get("email") or session.get("customer_email") or "",
                payment_mode="stripe",
                token_ttl_hours=settings.token_ttl_hours,
                download_limit=settings.download_limit,
            )
            app.logger.info("Webhook marked order %s as paid", order["checkout_ref"])

    return jsonify({"received": True})


@app.get("/download/<token>")
def download(token: str):
    platform = request.args.get("platform", "mac")
    normalized_platform = normalize_platform(platform)
    if is_stateless_mode():
        try:
            order = load_signed_download_token(token)
        except SignatureExpired:
            abort(403, "Download token expired.")
        except BadSignature:
            abort(404)

        app.logger.info("Serving stateless download to %s for order %s", order["email"], order["checkout_ref"])
        external_url, file_path = resolve_release_target(normalized_platform)
        if external_url:
            return redirect(external_url, code=302)
        if file_path is None:
            abort(500, "Download file missing.")
    else:
        order = ensure_db().get_order_by_token(token)
        if not order:
            abort(404)
        if order["payment_status"] != "paid":
            abort(403)

        expires_at = datetime.fromisoformat(order["token_expires_at"])
        if expires_at < datetime.now(UTC):
            abort(403, "Download token expired.")
        if order["download_count"] >= order["download_limit"]:
            abort(403, "Download limit reached.")
        external_url, file_path = resolve_release_target(normalized_platform)
        if not external_url and file_path is None:
            abort(500, "Download file missing.")

        ensure_db().increment_download_count(order["id"])
        app.logger.info(
            "Serving %s download to %s for order %s (%s/%s)",
            normalized_platform,
            order["email"],
            order["checkout_ref"],
            order["download_count"] + 1,
            order["download_limit"],
        )
        if external_url:
            return redirect(external_url, code=302)

    return send_file(
        file_path,
        as_attachment=True,
        download_name=get_release_filename(normalized_platform),
        mimetype="application/zip",
        max_age=0,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "8080")), debug=True)
