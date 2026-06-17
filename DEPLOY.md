# UcuncuGoz — Cloud Run Deploy Rehberi

Bu repo, GitHub baglantisi ile Cloud Run uzerine deploy edilecek sekilde hazirlanmistir. Backend ve frontend bagimsiz Cloud Run servisleridir.

## 1) On hazirlik (bir kez)

### Gerekli GCP API'leri

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  videointelligence.googleapis.com \
  storage.googleapis.com \
  sqladmin.googleapis.com   # Cloud SQL kullanacaksaniz
```

### Cloud Storage bucket

```bash
PROJECT_ID=$(gcloud config get-value project)
gcloud storage buckets create gs://ucuncugoz-videos \
  --location=europe-west1 \
  --uniform-bucket-level-access
```

> Bucket adi global tekildir; istediginiz benzersiz adi secin ve env'lerde tutarli kullanin.

### PostgreSQL

- **Onerilen:** Cloud SQL for PostgreSQL (kucuk bir `db-f1-micro` yeterli).
- Database URL: `postgresql+psycopg2://USER:PASSWORD@/ucuncugoz?host=/cloudsql/PROJECT:REGION:INSTANCE`
- Cloud Run deploy sirasinda `--add-cloudsql-instances=PROJECT:REGION:INSTANCE` flag'i ile bagla.

## 2) Servis hesabi (service account)

Tek bir runtime SA olusturmak en temizi:

```bash
gcloud iam service-accounts create ucuncugoz-runtime \
  --display-name="UcuncuGoz Cloud Run runtime"

SA="ucuncugoz-runtime@${PROJECT_ID}.iam.gserviceaccount.com"

# Gerekli IAM rolleri
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SA" --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SA" --role="roles/videointelligence.user"

# Cloud SQL kullaniyorsaniz:
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SA" --role="roles/cloudsql.client"
```

Backend kodu **kimligi `google.auth.default()` ile alir**: Cloud Run, kendi runtime SA'sini ADC olarak sunar — kodda anahtar dosyasi gerekmez.

## 3) Backend servisini deploy et

GitHub connect ile (Cloud Run > Create Service > Continuously deploy from a repository):

- **Source directory:** `/backend`
- **Build type:** Dockerfile (otomatik bulur)
- **Service name:** `ucuncugoz-backend`
- **Region:** `europe-west1` (bucket ile ayni bolge ideal)
- **CPU / Memory:** 1 CPU / 1 GiB iyi baslangic
- **Service account:** `ucuncugoz-runtime@...`
- **Allow unauthenticated invocations:** Evet (public API) — uretimde IAP ile kapatilabilir.
- **Cloud SQL connection:** (Cloud SQL kullaniyorsaniz) `--add-cloudsql-instances` veya Console secimi.

### Backend environment variables

| Var | Ornek |
|---|---|
| `DATABASE_URL` | `postgresql+psycopg2://user:pass@/ucuncugoz?host=/cloudsql/PROJECT:REGION:INSTANCE` |
| `GCP_PROJECT` | `<PROJECT_ID>` |
| `GCS_BUCKET` | `ucuncugoz-videos` |
| `VIDEO_INTELLIGENCE_MIN_CONFIDENCE` | `0.6` |
| `CORS_ORIGINS` | `https://ucuncugoz-frontend-<hash>-ew.a.run.app` (frontend deploy edilince tam URL'i girin) |

> `GOOGLE_APPLICATION_CREDENTIALS` **SET ETMEYIN** — runtime SA otomatik kullanilir.

Deploy sonrasi backend URL'sini not edin (`https://ucuncugoz-backend-<hash>-ew.a.run.app`).

## 4) Frontend servisini deploy et

Yine GitHub connect ile:

- **Source directory:** `/frontend`
- **Build type:** Dockerfile
- **Service name:** `ucuncugoz-frontend`
- **Region:** `europe-west1`
- **CPU / Memory:** 1 CPU / 512 MiB
- **Allow unauthenticated invocations:** Evet
- **Service account:** runtime SA (zorunlu degil, frontend GCP cagrisi yapmiyor)

### Frontend build argument (KRITIK)

`NEXT_PUBLIC_API_URL` Next.js tarafindan **build zamaninda** koda gomulur — sadece runtime env yetmez.

Cloud Run UI'da: **Build configuration > Build environment variables (substitutions)** kismina:

```
_NEXT_PUBLIC_API_URL = https://ucuncugoz-backend-<hash>-ew.a.run.app
```

Cloud Build, bu degeri Dockerfile'daki `ARG NEXT_PUBLIC_API_URL` icin `--build-arg` olarak gecmelidir. UI'dan secemiyorsaniz `cloudbuild.yaml` ekleyip explicit `args: ["--build-arg=NEXT_PUBLIC_API_URL=$_NEXT_PUBLIC_API_URL"]` verin.

Backend URL degisirse frontend'i **yeniden build** etmek gerekir.

## 5) CORS'u dogrula

Backend `CORS_ORIGINS`'i frontend Cloud Run URL'i ile guncelleyin. Soyle olmali:

```
CORS_ORIGINS=https://ucuncugoz-frontend-<hash>-ew.a.run.app
```

Birden fazla origin icin virgulle ayirin.

## 6) Smoke test

```bash
# Health
curl https://ucuncugoz-backend-<hash>-ew.a.run.app/health

# Frontend
open https://ucuncugoz-frontend-<hash>-ew.a.run.app
```

Bir MP4 yukleyin → "Analizi Baslat" → birkac dakika sonra sonuc sayfasinda araclar gozukmeli.

## Mimari notlar

- Video, frontend → backend → **GCS** akisinda yuklenir. Video Intelligence API GCS URI'sini (`gs://...`) dogrudan okur; gereksiz transcoding/indirme yoktur.
- OBJECT_TRACKING long-running operation olarak baslar; frontend `/status` endpoint'ini polling ile sorgular. Cloud Tasks/Pub-Sub callback'i bu sürum icin gereksiz (basit, durum-bazli).
- Video Intelligence cikan etiketleri `Car / Truck / Bus / Motorcycle` taksonomisine [video_intelligence.py](backend/app/services/video_intelligence.py) icindeki `VEHICLE_ENTITIES` + `VEHICLE_DISPLAY` map'i ile esler. Yeni sınıf eklemek isterseniz buraya ekleyin.

## Bilinen sinirlar / sonraki adimlar

- **CORS sımdilik frontend Cloud Run URL'i kadar dar tutulmali.** Custom domain eklerseniz CORS_ORIGINS'i guncelleyin.
- Video Intelligence ucretlidir; minimum confidence ve segment kısıtlamasıyla maliyeti dustırebilirsiniz.
- Buyuk dosyalar icin frontend → GCS dogrudan (signed URL) yuklemeye gecmek Cloud Run istek limiti (32 MiB POST) icin daha guvenli. Su an backend pass-through, kucuk videolar icin yeterli.
- Auth (kullanici girisi) yok; uretimde IAP veya Identity Platform onerilir.
