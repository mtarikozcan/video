# UcuncuGoz

Bulut tabanli arac tespit ve trafik analiz sistemi. Kullanici bir video yukler, sistem **Google Cloud Storage**'a koyar, **Google Video Intelligence API** (OBJECT_TRACKING) ile analiz eder ve tespit edilen araclari (Car, Truck, Bus, Motorcycle) zaman damgalariyla raporlar.

- **Backend:** Python 3.12 + FastAPI + SQLAlchemy + PostgreSQL
- **Frontend:** Next.js 14 + TypeScript + Tailwind + shadcn/ui + recharts
- **Bulut:** Google Cloud Storage + Video Intelligence API + Cloud Run (+ Cloud SQL on suggested deploy)

## Klasor yapisi

```
ucuncugoz/
├── backend/    # FastAPI uygulamasi + Dockerfile
├── frontend/   # Next.js uygulamasi + Dockerfile
├── DEPLOY.md   # Cloud Run deploy adimlari
└── README.md
```

## Lokal kurulum

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # degerleri doldur
uvicorn app.main:app --reload
```

Swagger: http://localhost:8000/docs · Health: http://localhost:8000/health

#### Backend env degiskenleri

| Degisken | Acıklama |
|---|---|
| `DATABASE_URL` | PostgreSQL baglanti URL'i. Lokal SQLite icin `sqlite:///./ucuncugoz.db` da gecerli. |
| `GCP_PROJECT` | GCP proje ID'si (opsiyonel; client default credential'dan da cikartir). |
| `GCS_BUCKET` | Video'larin yuklendigi Cloud Storage bucket adı. |
| `GOOGLE_APPLICATION_CREDENTIALS` | **Sadece lokal:** service account JSON anahtar dosyasinin mutlak yolu. Cloud Run'da bos birakin — runtime service account otomatik kullanilir. |
| `VIDEO_INTELLIGENCE_MIN_CONFIDENCE` | OBJECT_TRACKING icin minimum guven esigi (0-1, varsayilan 0.6). |
| `CORS_ORIGINS` | Virgulle ayrilmis frontend origin'leri. |

#### Lokal GCP kimligi

İki secenek:

1. **gcloud user credential'i** (en hizli yol):
   ```bash
   gcloud auth application-default login
   ```
   `GOOGLE_APPLICATION_CREDENTIALS` bos birakilabilir.

2. **Service account anahtari**:
   ```bash
   GOOGLE_APPLICATION_CREDENTIALS=/Users/you/keys/ucuncugoz-sa.json
   ```
   Hesap, en az `roles/storage.objectAdmin` + `roles/videointelligence.user` rollerine sahip olmali.

### Frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Uygulama: http://localhost:3000

| Degisken | Acıklama |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend URL'i (varsayilan `http://localhost:8000`). **Dikkat:** Next.js `NEXT_PUBLIC_*` env'leri build zamaninda gomulur; production icin Docker `build-arg` olarak verin. |

## Production deploy

Cloud Run uzerinde GitHub baglantili build ile deploy icin [`DEPLOY.md`](DEPLOY.md) dosyasina bakin.
