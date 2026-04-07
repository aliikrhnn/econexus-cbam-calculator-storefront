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
- `STORE_MAC_DOWNLOAD_URL`
- `STORE_WINDOWS_DOWNLOAD_URL`
- `STORE_MAC_SECURE_DOWNLOAD_URL`
- `STORE_WINDOWS_SECURE_DOWNLOAD_URL`
- `STORE_LICENSE_DURATION_DAYS=365`
- `PAYMENT_MODE=lemonsqueezy`
- `LEMON_SQUEEZY_API_KEY`
- `LEMON_SQUEEZY_STORE_ID`
- `LEMON_SQUEEZY_PRODUCT_ID`
- `LEMON_SQUEEZY_VARIANT_ID`

## İndirme dosyası

Vercel üzerinde uygulama dosyasını sunucu diski üzerinden vermeyin. Bunun yerine:

- Vercel Blob
- S3 / Cloudflare R2
- güvenli bir doğrudan dosya URL'si

kullanıp platform bazlı adresleri `STORE_MAC_DOWNLOAD_URL` ve `STORE_WINDOWS_DOWNLOAD_URL` içine koyun.

## Release artifact yapısı

Varsayılan yerel release klasörü:

```text
releases/
  CBAM_Engine_Mac.zip
  CBAM_Engine_Windows.zip
```

Varsayılan dosya adları:

- `CBAM_Engine_Mac.zip`
- `CBAM_Engine_Windows.zip`

Bu dosyalar mevcutsa:

- `/downloads` sayfasındaki macOS ve Windows butonları doğru dosyaya gider
- ödeme sonrası güvenli `/checkout/success` akışı da platform bazlı doğru dosyaya gider

İsterseniz dosyaları yerel klasörde tutmak yerine URL override kullanabilirsiniz:

- `STORE_MAC_DOWNLOAD_URL`
- `STORE_WINDOWS_DOWNLOAD_URL`

Güvenli post-payment akış için ayrı URL vermek isterseniz:

- `STORE_MAC_SECURE_DOWNLOAD_URL`
- `STORE_WINDOWS_SECURE_DOWNLOAD_URL`

## Download page

Projede artık ayrı bir indirme sayfası vardır:

```text
/downloads
```

Bu sayfa:

- macOS ve Windows linklerini ayrı gösterir
- yanlış dosya indirme riskini azaltır
- linkleri sadece environment variables üzerinden yönetir

İlgili ayarlar:

- `STORE_RELEASE_DIR`
- `STORE_MAC_RELEASE_FILENAME`
- `STORE_WINDOWS_RELEASE_FILENAME`
- `STORE_MAC_DOWNLOAD_URL`
- `STORE_WINDOWS_DOWNLOAD_URL`
- `STORE_MAC_SECURE_DOWNLOAD_URL`
- `STORE_WINDOWS_SECURE_DOWNLOAD_URL`
- `STORE_MAC_DOWNLOAD_NOTE`
- `STORE_WINDOWS_DOWNLOAD_NOTE`
- `STORE_RELEASE_VERSION`

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
STORE_RELEASE_DIR=/absolute/path/to/releases
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
- `releases/`: varsayılan macOS ve Windows ZIP release dosyaları
- `templates/`: Jinja şablonları
- `vercel.json`: Python runtime ayarı

## Not

Stateless `signed` modunda indirme linki süre bazlı korunur. SQLite tabanlı indirme sayacı mantığı Vercel üretim akışında kullanılmaz.

## Desktop lisans doğrulama

Ödeme sonrası kullanıcıya 1 yıl geçerli bir lisans anahtarı gösterilir. Desktop uygulama bu anahtarı
startup sırasında storefront üzerindeki `POST /api/license/validate` endpoint'i ile doğrular.

Desktop uygulamada aşağıdaki alan storefront domainine işaret etmelidir:

```text
CBAM_LICENSE_API_BASE_URL=https://your-domain.com
```
