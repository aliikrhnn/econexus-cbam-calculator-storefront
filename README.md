# CBAM Storefront

CBAM masaüstü uygulamasını satmak için hazırlanmış tek sayfalık satış sitesi.

Bu proje ana CBAM uygulamasından bağımsızdır ve GitHub üzerinden Vercel'e deploy edilecek şekilde ayarlanmıştır.

## Deploy modeli

Bu repo artık iki farklı çalışma modu destekler:

- `database`: Lokal geliştirme için SQLite tabanlı sipariş kaydı
- `signed`: Vercel için stateless, imzalı indirme linki

Vercel üzerinde kalıcı yerel disk güvenilir olmadığı için üretimde `signed` modu önerilir.

## Vercel için gerekenler

Vercel ortam değişkenlerinde en az şunları tanımlayın:

- `SECRET_KEY`
- `STORE_BASE_URL`
- `STORE_STORAGE_MODE=signed`
- `STORE_DOWNLOAD_URL`
- `PAYMENT_MODE=stripe`
- `STRIPE_SECRET_KEY`
- `STRIPE_PUBLISHABLE_KEY`
- `STRIPE_WEBHOOK_SECRET`

## İndirme dosyası

Vercel üzerinde uygulama dosyasını sunucu diski üzerinden vermeyin. Bunun yerine:

- Vercel Blob
- S3 / Cloudflare R2
- güvenli bir doğrudan dosya URL'si

kullanıp bu adresi `STORE_DOWNLOAD_URL` içine koyun.

`STORE_DOWNLOAD_FILE` sadece lokal geliştirme için uygundur.

## Lokal geliştirme

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python storefront/app.py
```

Lokal kullanım için örnek ayar:

```env
STORE_STORAGE_MODE=database
PAYMENT_MODE=demo
STORE_DOWNLOAD_FILE=/absolute/path/to/CBAM_Engine_Mac.zip
```

## Vercel deploy akışı

1. Bu klasörü GitHub'a yükle
2. Vercel'de projeyi GitHub repo üzerinden import et
3. Root dizin olarak bu projeyi seç
4. Environment Variables bölümüne gerekli değerleri gir
5. Stripe webhook adresini şu endpoint'e bağla:

```text
https://your-domain.com/webhooks/stripe
```

## Dosya yapısı

- `app.py`: Vercel entry point
- `storefront/app.py`: Flask uygulaması
- `public/styles.css`: Vercel ve lokal kullanım için public CSS
- `templates/`: Jinja şablonları
- `vercel.json`: Python runtime ayarı

## Not

Stateless `signed` modunda indirme linki süre bazlı korunur. SQLite tabanlı indirme sayacı mantığı Vercel üretim akışında kullanılmaz.
