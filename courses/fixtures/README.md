# Fixtures untuk Kursus Online

Fixtures ini berisi data lengkap untuk aplikasi pembelajaran online, termasuk:

- **5 Subject (Mata Pelajaran)**: Pemrograman, Matematika, Fisika, Bahasa, Desain
- **6 Courses (Kursus)**: Python untuk Pemula, Django Web Development, JavaScript Modern, Kalkulus Dasar, Aljabar
  Linear, UI/UX Design Fundamentals
- **22 Modules (Modul)**: Setiap kursus memiliki 3-4 modul pembelajaran
- **30+ Text Content**: Materi pembelajaran dalam format teks
- **18+ Video Content**: Link video pembelajaran
- **48+ Content Items**: Konten yang terhubung dengan modul-modulnya

## Struktur Fixtures

```
fixtures/
├── subjects.json          # 5 mata pelajaran
├── courses.json           # 6 kursus
├── modules.json           # 22 modul
├── texts.json             # 30+ konten teks
├── videos.json            # 18+ konten video
├── contents.json          # 48+ item konten yang terhubung ke modul
├── load_all_fixtures.sh   # Script untuk load semua fixtures
└── README.md              # File ini
```

## Detail Kursus

### 1. Python untuk Pemula (4 modul)

- Pengenalan Python
- Tipe Data dan Variabel
- Struktur Kontrol
- Fungsi dan Module

### 2. Django Web Development (4 modul)

- Setup Django Project
- Models dan Database
- Views dan Templates
- Forms dan Validasi

### 3. JavaScript Modern (4 modul)

- JavaScript Basics
- ES6+ Features
- DOM Manipulation
- Async JavaScript

### 4. Kalkulus Dasar (3 modul)

- Limit dan Kontinuitas
- Turunan
- Integral

### 5. Aljabar Linear (3 modul)

- Vektor dan Matriks
- Sistem Persamaan Linear
- Eigenvalue dan Eigenvector

### 6. UI/UX Design Fundamentals (4 modul)

- Prinsip Desain
- User Research
- Wireframing dan Prototyping
- Usability Testing

## Cara Menggunakan

### Load semua fixtures sekaligus (Recommended):

```bash
# Pastikan Anda sudah membuat user dengan ID=1 terlebih dahulu
# Atau sesuaikan owner di fixtures dengan user yang ada

# Jalankan script
bash courses/fixtures/load_all_fixtures.sh
```

### Load fixtures satu per satu (Manual):

```bash
# 1. Load subjects terlebih dahulu
python manage.py loaddata courses/fixtures/subjects.json

# 2. Load courses (memerlukan subjects dan user)
python manage.py loaddata courses/fixtures/courses.json

# 3. Load modules (memerlukan courses)
python manage.py loaddata courses/fixtures/modules.json

# 4. Load text dan video content (memerlukan user)
python manage.py loaddata courses/fixtures/texts.json
python manage.py loaddata courses/fixtures/videos.json

# 5. Load content items terakhir (memerlukan modules dan content)
python manage.py loaddata courses/fixtures/contents.json
```

## Catatan Penting

1. **User Requirement**: Semua fixtures menggunakan `owner: 1`, pastikan Anda memiliki user dengan ID=1 di database.
   Jika belum ada, buat dulu:

```bash
python manage.py createsuperuser
```

2. **Urutan Loading**: Sangat penting untuk load fixtures dalam urutan yang benar karena ada foreign key dependencies:
    - subjects.json (tidak ada dependency)
    - courses.json (memerlukan subjects dan user)
    - modules.json (memerlukan courses)
    - texts.json dan videos.json (memerlukan user)
    - contents.json (memerlukan modules, texts, videos, dan ContentType)

3. **ContentType**: Fixtures `contents.json` menggunakan GenericForeignKey. Django akan otomatis handle ContentType saat
   loading.

## Reset Database (Opsional)

Jika ingin mereset semua data kursus:

```bash
# Hapus data existing (hati-hati!)
python manage.py shell -c "
from courses.models import Subject, Course, Module, Content, Text, Video, Image, File
Content.objects.all().delete()
Text.objects.all().delete()
Video.objects.all().delete()
Image.objects.all().delete()
File.objects.all().delete()
Module.objects.all().delete()
Course.objects.all().delete()
Subject.objects.all().delete()
print('Data kursus berhasil dihapus')
"

# Kemudian load fixtures baru
bash courses/fixtures/load_all_fixtures.sh
```

## Troubleshooting

### Error: "Cannot assign: User matching query does not exist"

**Solusi**: Buat user dengan ID=1 atau edit fixtures untuk menggunakan ID user yang ada.

### Error: "ContentType matching query does not exist"

**Solusi**: Pastikan Anda sudah menjalankan migrations dengan benar:

```bash
python manage.py migrate
```

### Error: Foreign Key constraints

**Solusi**: Load fixtures dalam urutan yang benar sesuai dengan dependencies.

## Customisasi

Anda bisa menambahkan lebih banyak konten dengan:

1. Membuat text/video content baru di file texts.json atau videos.json
2. Menambahkan modul baru di modules.json
3. Menghubungkan content dengan modul di contents.json
4. Sesuaikan `order` field untuk mengatur urutan tampilan

## Lisensi

Data fixtures ini dibuat untuk keperluan pembelajaran dan development.

