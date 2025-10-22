# Panduan Konfigurasi Settings untuk ta3lem LMS

## Struktur Settings

Settings telah dibagi menjadi beberapa file untuk memudahkan manajemen di berbagai environment:

```
ta3lem/settings/
├── __init__.py          # Entry point, load settings berdasarkan DJANGO_ENV
├── base.py              # Settings umum untuk semua environment
├── development.py       # Settings untuk development/local
├── staging.py           # Settings untuk staging
└── production.py        # Settings untuk production
```

## Cara Menggunakan

### 1. Development (Default)

Untuk development, tidak perlu konfigurasi tambahan. Cukup jalankan:

```bash
python manage.py runserver
```

Atau set environment variable secara eksplisit:

```bash
export DJANGO_ENV=development
python manage.py runserver
```

**Features Development:**
- DEBUG = True
- SQLite database
- Django Debug Toolbar aktif
- Redis board aktif
- Email dikirim ke console
- Secret key hardcoded (tidak aman, hanya untuk dev)

### 2. Staging

Untuk staging environment:

```bash
# Set environment variable
export DJANGO_ENV=staging

# Set environment variables lainnya
export DJANGO_SECRET_KEY='your-secret-key-staging'
export DJANGO_ALLOWED_HOSTS='staging.ta3lem.com'
export DB_NAME='ta3lem_staging'
export DB_USER='postgres'
export DB_PASSWORD='your-password'
# ... dst

# Atau gunakan file .env dengan python-decouple atau django-environ

python manage.py migrate
python manage.py collectstatic
python manage.py runserver
```

**Features Staging:**
- DEBUG = False (default, bisa diubah via env)
- PostgreSQL database
- Redis cache
- Email via SMTP
- Security settings medium level
- Logging ke file

### 3. Production

Untuk production environment:

```bash
# Set environment variable
export DJANGO_ENV=production

# WAJIB set environment variables berikut:
export DJANGO_SECRET_KEY='your-very-secure-secret-key'
export DJANGO_ALLOWED_HOSTS='ta3lem.com,www.ta3lem.com'
export DB_NAME='ta3lem_production'
export DB_USER='postgres'
export DB_PASSWORD='your-strong-password'
export DB_HOST='your-db-host'
export REDIS_URL='redis://your-redis-host:6379/0'
export EMAIL_HOST_USER='your-email@gmail.com'
export EMAIL_HOST_PASSWORD='your-email-password'
# ... dst

python manage.py migrate
python manage.py collectstatic --noinput
gunicorn ta3lem.wsgi:application
```

**Features Production:**
- DEBUG = False (strict)
- PostgreSQL database (required)
- Redis cache dengan persistence
- Email via SMTP (required)
- Maximum security settings (SSL, HSTS, secure cookies)
- Comprehensive logging
- Admin email notifications untuk errors

## Environment Variables

Lihat file `.env.example` untuk daftar lengkap environment variables yang tersedia.

### Minimal Environment Variables untuk Production:

```bash
DJANGO_ENV=production
DJANGO_SECRET_KEY=<generate dengan: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'>
DJANGO_ALLOWED_HOSTS=yourdomain.com
DB_NAME=ta3lem_production
DB_USER=postgres
DB_PASSWORD=<your-password>
DB_HOST=<your-db-host>
REDIS_URL=redis://<your-redis-host>:6379/0
EMAIL_HOST_USER=<your-email>
EMAIL_HOST_PASSWORD=<your-email-password>
```

## Migrasi dari settings.py Lama

File `settings.py` lama telah diganti dengan struktur folder. Jika ada masalah, backup ada di:
- `ta3lem/settings.py.backup` (jika diperlukan)

Untuk kembali ke settings lama, hapus folder `ta3lem/settings/` dan restore dari backup.

## Tips

### Generate Secret Key Baru:

```python
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### Test Settings untuk Environment Tertentu:

```bash
DJANGO_ENV=staging python manage.py check
DJANGO_ENV=production python manage.py check --deploy
```

### Setup Logs Directory:

```bash
mkdir -p logs
```

### Install Dependencies untuk Production:

Jika menggunakan PostgreSQL:
```bash
pip install psycopg2-binary
```

Jika menggunakan django-redis:
```bash
pip install django-redis
```

## Troubleshooting

### ImportError: No module named ta3lem.settings

Pastikan folder `ta3lem/settings/` memiliki file `__init__.py`

### SECRET_KEY atau ALLOWED_HOSTS error di production

Set environment variable yang required. Lihat error message untuk detail.

### Database connection error

Pastikan PostgreSQL sudah running dan credentials sudah benar di environment variables.

## Keamanan

⚠️ **PENTING:**
- Jangan commit file `.env` ke git
- Tambahkan `.env` ke `.gitignore`
- Gunakan secret key yang berbeda untuk setiap environment
- Gunakan environment variables atau secret management service untuk production
- Aktifkan SSL/HTTPS di production

