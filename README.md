# UcuncuGoz

Bulut tabanli arac tespit ve trafik analiz sistemi. Kullanici bir video yukler, sistem AWS S3'e koyar, AWS Rekognition Video ile analiz eder ve tespit edilen araclari (Car, Truck, Bus, Motorcycle) zaman damgalariyla raporlar.

- Backend: Python 3.11+ / FastAPI / boto3 / SQLAlchemy / PostgreSQL
- Frontend: Next.js 14 + TypeScript + Tailwind + shadcn/ui + recharts
- Bulut: AWS S3 + AWS Rekognition Video + AWS RDS

## Klasor yapisi

```
ucuncugoz/
├── backend/   # FastAPI uygulamasi
├── frontend/  # Next.js uygulamasi
└── README.md
```

## Backend kurulumu

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # degerleri doldur
uvicorn app.main:app --reload
```

Swagger: http://localhost:8000/docs  · Health: http://localhost:8000/health

### Gerekli ortam degiskenleri

| Degisken | Acıklama |
|----------|----------|
| `DATABASE_URL` | PostgreSQL baglanti URL'i (ornek: `postgresql+psycopg2://postgres:postgres@localhost:5432/ucuncugoz`) |
| `AWS_REGION` | AWS bolgesi (ornek: `eu-central-1`) |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | AWS kimligi (local gelistirme icin; EC2'de IAM Role kullanilir) |
| `S3_BUCKET` | Video yukleme bucket adı |
| `REKOGNITION_MIN_CONFIDENCE` | Etiket minimum guven skoru (varsayilan 70) |
| `REKOGNITION_ROLE_ARN` | Rekognition'in SNS topic'ine yazabilmesi icin IAM rol ARN'i (opsiyonel, async job icin gerekir) |
| `CORS_ORIGINS` | Virgulle ayrilmis frontend origin'leri |

### Local PostgreSQL

```bash
createdb ucuncugoz
```

Tablolar Slice 2 sonrasinda `database.py` icinden olusturulur.

## Frontend kurulumu

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Uygulama: http://localhost:3000

| Degisken | Acıklama |
|----------|----------|
| `NEXT_PUBLIC_API_BASE_URL` | Backend URL'i (varsayilan `http://localhost:8000`) |

## Sonraki adimlar

Bu repo local gelistirme icindir. AWS uretim kurulumu (S3 bucket, RDS, EC2, IAM rolleri) ayri yapilacaktir.
