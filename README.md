# EcoNexus CBAM — Storefront

The sales and licensing storefront for a desktop CBAM calculator: it takes payment, issues
a time-limited licence and serves the application download over signed, expiring links.

The EU **Carbon Border Adjustment Mechanism** requires importers of goods such as steel,
cement, aluminium and fertiliser to report the embedded emissions of what they bring into
the Union, and eventually to surrender certificates against them. The desktop tool does
that calculation. This repository is everything around it — the part that sells it.

## What it handles

- Single-page product and pricing site
- Checkout through Lemon Squeezy, with Stripe supported as an alternative
- Licence issuance on successful payment, with a configurable duration
  (`STORE_LICENSE_DURATION_DAYS`, default 365)
- Signed, expiring download URLs for the macOS and Windows builds
- Order records, with release artefacts tracked in `releases/`

## Two storage modes

The interesting constraint in this repository is that it deploys to Vercel, where there
is no reliable persistent local disk and no long-lived process. So it ships two modes:

| Mode | Behaviour | Use |
| --- | --- | --- |
| `database` | SQLite-backed order records | Local development |
| `signed` | Stateless — the download grant is a signed, expiring token, verified on request | Production on Vercel |

In `signed` mode nothing is written to disk. The entitlement is carried in a MAC-signed
token, so a link is valid, attributable and expires without any server-side session to
keep. Binaries are served from object storage (Vercel Blob, S3 or R2) rather than from the
application.

## Stack

Python · Flask · Stripe / Lemon Squeezy · pytest · Vercel

## Running it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then fill it in
flask --app app run           # http://localhost:5000
```

```bash
pytest
```

## Configuration

| Variable | |
| --- | --- |
| `SECRET_KEY` | Signing key for download tokens |
| `STORE_BASE_URL` | Public base URL |
| `STORE_STORAGE_MODE` | `database` or `signed` |
| `STORE_MAC_DOWNLOAD_URL` / `STORE_WINDOWS_DOWNLOAD_URL` | Build locations |
| `STORE_MAC_SECURE_DOWNLOAD_URL` / `STORE_WINDOWS_SECURE_DOWNLOAD_URL` | Signed variants |
| `STORE_LICENSE_DURATION_DAYS` | Licence validity, default `365` |
| `PAYMENT_MODE` | `lemonsqueezy` or `stripe` |
| `LEMON_SQUEEZY_API_KEY` / `_STORE_ID` / `_PRODUCT_ID` / `_VARIANT_ID` | Lemon Squeezy config |

## Notes

This repository is independent of the CBAM desktop application itself and deploys on its
own. Serving the build from the application's own filesystem is deliberately not
supported in production.

## Licence

Not open source. Published for review; all rights reserved.
