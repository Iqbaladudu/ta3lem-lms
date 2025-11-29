# ✅ Manual Testing Checklist - Course Management untuk Instruktur

## 📋 Persiapan Awal

### Setup Environment
- [ ] Server Django sudah berjalan di `http://localhost:8000`
- [ ] Database sudah dimigrate dan ada data fixtures
- [ ] Sudah memiliki akun instruktur (role: instructor)
- [ ] Browser developer tools sudah terbuka (untuk cek error console)
- [ ] Siapkan notepad untuk mencatat bug/issue

### Test Data yang Diperlukan
- [ ] Minimal 3 kursus dengan owner instruktur yang sedang login
- [ ] Minimal 2 subject berbeda
- [ ] Kursus dengan minimal 3 module
- [ ] Setiap module minimal punya 2-3 content (text, video, image, file)
- [ ] Minimal 3 siswa yang enrolled di berbagai kursus
- [ ] Beberapa siswa dengan progress berbeda (0%, 50%, 100%)

---

## 🎯 SECTION 1: DASHBOARD INSTRUKTUR

### URL: `/courses/mine/`

#### 1.1 Akses Halaman
- [ ] Login sebagai instruktur
- [ ] Navigasi ke `/courses/mine/`
- [ ] Halaman berhasil dimuat tanpa error
- [ ] URL redirect ke login jika belum login

#### 1.2 Header Section
- [ ] Header gradient biru-ungu-pink muncul dengan baik
- [ ] Judul "Kelola Kursus Saya" tampil
- [ ] Tombol "Kelola Siswa" tampil dan terlihat jelas
- [ ] Klik tombol "Kelola Siswa" → redirect ke `/courses/students/overview/`
- [ ] Tombol "Buat Kursus Baru" tampil
- [ ] Klik "Buat Kursus Baru" → redirect ke form pembuatan kursus

#### 1.3 Statistics Cards
- [ ] 4 cards statistik tampil (Total Kursus, Total Modul, Total Siswa, Total Konten)
- [ ] Angka pada setiap card sesuai dengan data aktual
- [ ] Card "Total Siswa" memiliki cursor pointer (clickable)
- [ ] Klik card "Total Siswa" → redirect ke student overview
- [ ] Gradient dan shadow effects tampil dengan baik
- [ ] Responsive di mobile (cards stack secara vertikal)

#### 1.4 Search Functionality
- [ ] Search bar tampil di atas daftar kursus
- [ ] Ketik nama kursus → hasil filter secara real-time
- [ ] Ketik overview kursus → hasil filter muncul
- [ ] Ketik nama subject → kursus dengan subject tersebut muncul
- [ ] Clear search → semua kursus muncul kembali
- [ ] Search dengan kata yang tidak ada → tampil "Tidak ada kursus yang ditemukan"

#### 1.5 Course Cards
- [ ] Semua kursus milik instruktur tampil
- [ ] Setiap card menampilkan:
  - [ ] Judul kursus
  - [ ] Subject badge (warna berbeda per subject)
  - [ ] Overview/deskripsi singkat
  - [ ] Jumlah modul
  - [ ] Jumlah siswa
  - [ ] Tanggal dibuat
- [ ] Card memiliki hover effect (shadow lebih besar)
- [ ] Kursus terurut berdasarkan tanggal dibuat (terbaru di atas)

#### 1.6 Action Buttons per Course
**Baris Pertama:**
- [ ] Tombol "Edit" (hijau) → redirect ke `/courses/<id>/edit/`
- [ ] Tombol "Modul" (biru) → redirect ke `/courses/<id>/module/`
- [ ] Tombol "Hapus" (merah) → muncul konfirmasi delete

**Baris Kedua:**
- [ ] Tombol "Analytics" (ungu) → redirect ke `/courses/analytics/<id>/`
- [ ] Tombol "Siswa" (teal) → redirect ke `/courses/students/<id>/`

#### 1.7 Delete Course
- [ ] Klik tombol "Hapus"
- [ ] Muncul modal/konfirmasi delete
- [ ] Konfirmasi delete → kursus terhapus dari list
- [ ] Cancel delete → kursus tetap ada
- [ ] Setelah delete, statistik cards terupdate

---

## 📝 SECTION 2: COURSE CRUD OPERATIONS

### 2.1 Create Course
**URL:** `/courses/create/`

- [ ] Akses halaman create
- [ ] Form tampil dengan field: Subject, Title, Slug, Overview
- [ ] Semua field required berfungsi (tidak bisa submit kosong)
- [ ] Pilih subject dari dropdown
- [ ] Isi title → slug auto-generate
- [ ] Isi overview dengan teks panjang
- [ ] Submit form → kursus baru muncul di dashboard
- [ ] Kursus baru memiliki owner = instruktur yang sedang login
- [ ] Redirect ke `/courses/mine/` setelah sukses
- [ ] Test error handling: submit dengan slug yang sudah ada

### 2.2 Update Course
**URL:** `/courses/<id>/edit/`

- [ ] Klik "Edit" pada salah satu course
- [ ] Form pre-filled dengan data kursus existing
- [ ] Ubah title → simpan → perubahan tersimpan
- [ ] Ubah subject → simpan → subject terupdate
- [ ] Ubah overview → simpan → overview terupdate
- [ ] Ubah slug → simpan → slug terupdate
- [ ] Cancel → kembali ke dashboard tanpa perubahan
- [ ] Test error: ubah slug jadi duplikat → error message muncul

### 2.3 Delete Course
**URL:** `/courses/<id>/delete/`

- [ ] Klik "Hapus" dari dashboard
- [ ] Halaman konfirmasi delete tampil
- [ ] Informasi kursus yang akan dihapus tampil
- [ ] Klik "Confirm Delete" → kursus terhapus
- [ ] Redirect ke dashboard
- [ ] Kursus tidak muncul lagi di list
- [ ] Klik "Cancel" → kembali ke dashboard tanpa delete
- [ ] Cek cascade delete: module dan content ikut terhapus

---

## 🎓 SECTION 3: MODULE MANAGEMENT

### 3.1 Module List/Update
**URL:** `/courses/<id>/module/`

- [ ] Akses halaman module management
- [ ] Formset modules tampil
- [ ] Semua module existing tampil di form
- [ ] Setiap module menampilkan: title, description, order
- [ ] Bisa menambah module baru (klik "Add module")
- [ ] Bisa menghapus module (checkbox delete)
- [ ] Bisa mengubah order module
- [ ] Ubah title module → simpan → perubahan tersimpan
- [ ] Ubah description → simpan → terupdate
- [ ] Tambah module baru → simpan → module baru muncul
- [ ] Delete module → simpan → module terhapus
- [ ] Test validation: title kosong → error message

### 3.2 Module Ordering (Drag & Drop)
- [ ] Module list mendukung drag & drop (jika ada fitur ini)
- [ ] Drag module ke posisi baru
- [ ] Drop module → order terupdate via AJAX
- [ ] Refresh halaman → order tetap tersimpan
- [ ] Order number tampil di setiap module
- [ ] Check console untuk AJAX error

### 3.3 Module Content List
**URL:** `/courses/module/<module_id>/`

- [ ] Klik salah satu module untuk lihat contents
- [ ] Daftar content di module tampil
- [ ] Setiap content menampilkan:
  - [ ] Icon sesuai tipe (text, video, image, file)
  - [ ] Title content
  - [ ] Order number
  - [ ] Action buttons (Edit, Delete)
- [ ] Content terurut berdasarkan order
- [ ] Tombol "Add content" untuk setiap tipe (Text, Video, Image, File)

---

## 📄 SECTION 4: CONTENT MANAGEMENT

### 4.1 Create Text Content
**URL:** `/courses/module/<module_id>/content/text/create/`

- [ ] Klik "Add Text Content"
- [ ] Form create text tampil
- [ ] Field: Title, Content (textarea)
- [ ] Isi title dan content
- [ ] Submit → content baru muncul di module content list
- [ ] Content type = "text"
- [ ] Order otomatis terisi
- [ ] Owner = instruktur yang login

### 4.2 Create Video Content
**URL:** `/courses/module/<module_id>/content/video/create/`

- [ ] Klik "Add Video Content"
- [ ] Form create video tampil
- [ ] Field: Title, URL (video URL)
- [ ] Isi title dan URL YouTube/Vimeo
- [ ] Submit → video content muncul di list
- [ ] Test dengan URL valid dan invalid
- [ ] URL invalid → error validation

### 4.3 Create Image Content
**URL:** `/courses/module/<module_id>/content/image/create/`

- [ ] Klik "Add Image Content"
- [ ] Form upload image tampil
- [ ] Field: Title, File (image upload)
- [ ] Pilih file image (jpg, png, gif)
- [ ] Submit → image terupload
- [ ] Image tersimpan di media/images/
- [ ] Test dengan file non-image → error validation
- [ ] Test dengan file size besar

### 4.4 Create File Content
**URL:** `/courses/module/<module_id>/content/file/create/`

- [ ] Klik "Add File Content"
- [ ] Form upload file tampil
- [ ] Field: Title, File (file upload)
- [ ] Upload PDF/document
- [ ] Submit → file terupload
- [ ] File tersimpan di media/files/
- [ ] Test dengan berbagai tipe file (pdf, docx, pptx)

### 4.5 Update Content
**URL:** `/courses/module/<module_id>/content/<type>/<id>/`

- [ ] Klik "Edit" pada salah satu content
- [ ] Form pre-filled dengan data existing
- [ ] Ubah title → simpan → terupdate
- [ ] Ubah content/URL/file → simpan → terupdate
- [ ] Test untuk semua tipe content (text, video, image, file)

### 4.6 Delete Content
**URL:** `/courses/content/<id>/delete/`

- [ ] Klik "Delete" pada content
- [ ] Konfirmasi delete (jika ada)
- [ ] Content terhapus dari list
- [ ] File terupload (image/file) ikut terhapus dari storage
- [ ] Order content lain tetap konsisten

### 4.7 Content Ordering
- [ ] Content mendukung drag & drop (jika ada)
- [ ] Drag content ke posisi baru
- [ ] Order terupdate via AJAX
- [ ] Refresh → order tetap tersimpan

---

## 👥 SECTION 5: STUDENT MANAGEMENT

### 5.1 Students Overview
**URL:** `/courses/students/overview/`

#### Access & Navigation
- [ ] Klik "Kelola Siswa" dari dashboard → berhasil redirect
- [ ] Klik card "Total Siswa" → berhasil redirect
- [ ] Direct URL access → halaman tampil

#### Header & Statistics
- [ ] Header gradient tampil dengan baik
- [ ] Judul "Kelola Siswa - Semua Kursus" tampil
- [ ] 4 statistics cards:
  - [ ] Total Siswa Unik (angka benar)
  - [ ] Pendaftaran Aktif (angka benar)
  - [ ] Pendaftaran Selesai (angka benar)
  - [ ] Rata-rata Progress (persentase benar)
- [ ] Tombol "Kembali ke Dashboard" berfungsi

#### Student List
- [ ] Semua siswa unik tampil (tidak duplikat)
- [ ] Setiap student card menampilkan:
  - [ ] Avatar dengan inisial
  - [ ] Username
  - [ ] Email (jika ada)
  - [ ] Total kursus yang diikuti
  - [ ] Kursus aktif/selesai
  - [ ] Rata-rata progress (angka dan bar)
  - [ ] Kursus terakhir diakses
  - [ ] Waktu akses terakhir (format: "2 jam yang lalu")
- [ ] Preview maksimal 3 kursus per siswa
- [ ] Siswa terurut berdasarkan last_accessed (terbaru dulu)

#### Sidebar - Course Statistics
- [ ] Sidebar menampilkan semua kursus instruktur
- [ ] Setiap course card di sidebar menampilkan:
  - [ ] Judul kursus
  - [ ] Total siswa
  - [ ] Siswa aktif dan selesai
  - [ ] Rata-rata progress
  - [ ] Tombol "Detail"
- [ ] Klik "Detail" → redirect ke course students page
- [ ] Statistik per kursus akurat

#### Responsive Design
- [ ] Desktop view (≥1024px) → sidebar di kanan
- [ ] Tablet view (768-1023px) → layout adjust
- [ ] Mobile view (<768px) → sidebar di bawah, stack vertikal

### 5.2 Course Students
**URL:** `/courses/students/<course_id>/`

#### Access & Navigation
- [ ] Klik tombol "Siswa" dari course card di dashboard
- [ ] Klik "Detail" dari students overview sidebar
- [ ] Direct URL dengan course_id valid
- [ ] Test dengan course_id yang bukan milik instruktur → error 403/404

#### Header & Breadcrumb
- [ ] Judul kursus tampil di header
- [ ] Breadcrumb: Dashboard > Manajemen Siswa > [Nama Kursus]
- [ ] Tombol "Kembali ke Manajemen Siswa" berfungsi
- [ ] Tombol "Analytics" redirect ke course analytics

#### Statistics Cards
- [ ] Total Siswa (sesuai enrollment count)
- [ ] Siswa Aktif (status = enrolled)
- [ ] Siswa Selesai (status = completed)
- [ ] Rata-rata Progress (dihitung dari semua enrollments)

#### Student Cards
- [ ] Semua siswa enrolled tampil
- [ ] Setiap student card menampilkan:
  - [ ] Username dan avatar
  - [ ] Status badge (warna: hijau=enrolled, kuning=completed, abu=paused)
  - [ ] Tanggal enrollment
  - [ ] Progress percentage dengan bar
  - [ ] Modul selesai / Total modul
  - [ ] Konten selesai / Total konten
  - [ ] Sesi belajar terbaru (max 2)
- [ ] Progress bar sesuai dengan persentase
- [ ] Status badge warna konsisten
- [ ] Tombol "Lihat Detail Progress" berfungsi

#### Sidebar - Module Statistics
- [ ] Daftar semua module di kursus
- [ ] Setiap module menampilkan:
  - [ ] Title dan order
  - [ ] Completion rate (%)
  - [ ] Siswa yang menyelesaikan / Total siswa
  - [ ] Progress bar
- [ ] Completion rate dihitung dengan benar
- [ ] Module terurut berdasarkan order
- [ ] Info kursus: total module, subject

#### Responsive Design
- [ ] Responsive di berbagai ukuran layar
- [ ] Mobile: sidebar di bawah
- [ ] Desktop: sidebar di kanan

---

## 📊 SECTION 6: ANALYTICS

### 6.1 Course Analytics
**URL:** `/courses/analytics/<course_id>/`

#### Access
- [ ] Klik tombol "Analytics" dari course card
- [ ] Klik "Analytics" dari course students page
- [ ] Direct URL access

#### Overall Statistics
- [ ] Total siswa enrolled
- [ ] Rata-rata completion rate
- [ ] Total sesi belajar
- [ ] Rata-rata waktu belajar (jika ada)
- [ ] Chart/grafik progress (jika ada)

#### Module Analytics
- [ ] Daftar module dengan completion rate
- [ ] Siswa yang menyelesaikan per module
- [ ] Most completed module
- [ ] Least completed module

#### Student List in Analytics
- [ ] Daftar semua siswa dengan progress
- [ ] Sort by progress (ascending/descending)
- [ ] Filter by status
- [ ] Link ke student detail progress

### 6.2 Student Progress Detail
**URL:** `/courses/analytics/<course_id>/student/<student_id>/`

#### Access
- [ ] Klik "Lihat Detail Progress" dari course students
- [ ] Klik student dari analytics page
- [ ] Direct URL access

#### Student Information
- [ ] Username, email, avatar
- [ ] Enrollment date
- [ ] Last accessed date
- [ ] Overall progress percentage
- [ ] Status (enrolled/completed/paused)

#### Module-by-Module Progress
- [ ] Daftar semua module
- [ ] Setiap module menampilkan:
  - [ ] Module title
  - [ ] Completion status (completed/in progress/not started)
  - [ ] Content progress per module
  - [ ] List content dengan status completed/incomplete
- [ ] Visual indicator (check/cross) untuk setiap content

#### Learning Sessions
- [ ] Daftar learning sessions
- [ ] Setiap session menampilkan:
  - [ ] Waktu mulai
  - [ ] Waktu selesai (jika ada)
  - [ ] Duration (jika ada)
  - [ ] Content yang diakses
- [ ] Sessions terurut dari terbaru

---

## 🔄 SECTION 7: INTEGRATION TESTING

### 7.1 Complete Workflow: Buat Kursus Lengkap
1. [ ] Login sebagai instruktur
2. [ ] Buat kursus baru
3. [ ] Tambah 3 module
4. [ ] Setiap module, tambah minimal 2 content (berbeda tipe)
5. [ ] Cek di course list → kursus baru muncul
6. [ ] Edit course → ubah title
7. [ ] Cek di module list → semua module dan content ada
8. [ ] Test reorder module
9. [ ] Test reorder content
10. [ ] Kursus siap untuk enrollment siswa

### 7.2 Complete Workflow: Monitor Student Progress
1. [ ] Login sebagai siswa
2. [ ] Enroll ke kursus
3. [ ] Akses beberapa content
4. [ ] Mark beberapa content sebagai complete
5. [ ] Logout
6. [ ] Login sebagai instruktur (owner kursus)
7. [ ] Cek Students Overview → siswa muncul
8. [ ] Cek Course Students → progress siswa tampil
9. [ ] Cek Student Detail → progress detail akurat
10. [ ] Cek Analytics → data konsisten

### 7.3 Cross-browser Testing
- [ ] Chrome: semua fitur berfungsi
- [ ] Firefox: semua fitur berfungsi
- [ ] Safari: semua fitur berfungsi (jika di Mac)
- [ ] Edge: semua fitur berfungsi
- [ ] Mobile Chrome (Android): responsive berfungsi
- [ ] Mobile Safari (iOS): responsive berfungsi

---

## 🐛 SECTION 8: ERROR HANDLING & EDGE CASES

### 8.1 Permission Testing
- [ ] User tanpa role instructor → akses `/courses/mine/` → redirect/403
- [ ] Instruktur A akses kursus milik Instruktur B → error 403
- [ ] Student akses instructor pages → redirect/403
- [ ] Anonymous user akses instructor pages → redirect ke login

### 8.2 Empty State Testing
- [ ] Instruktur baru tanpa kursus → dashboard tampil empty state
- [ ] Kursus tanpa module → module list empty
- [ ] Module tanpa content → content list empty
- [ ] Kursus tanpa siswa → student list empty
- [ ] Students overview tanpa siswa → empty state

### 8.3 Data Validation
- [ ] Submit form dengan field kosong → validation error
- [ ] Upload file dengan size terlalu besar → error message
- [ ] Upload file dengan tipe tidak valid → error message
- [ ] Slug duplikat → error message
- [ ] URL video tidak valid → error message

### 8.4 Network Error Testing
- [ ] Matikan internet saat drag & drop → error handling
- [ ] Matikan internet saat submit form → error handling
- [ ] Slow network → loading indicator muncul

---

## 📱 SECTION 9: UI/UX TESTING

### 9.1 Visual Testing
- [ ] Gradient colors konsisten di semua page
- [ ] Font sizes readable di semua device
- [ ] Button sizes touchable di mobile (min 44x44px)
- [ ] Icons tampil dengan benar
- [ ] Images tidak pecah/blur
- [ ] Colors accessible (contrast ratio cukup)

### 9.2 Interaction Testing
- [ ] Hover effects smooth
- [ ] Button click feedback (active state)
- [ ] Form focus states jelas
- [ ] Transitions tidak janky
- [ ] No layout shift saat loading
- [ ] Modal/dialog muncul dengan animasi smooth

### 9.3 Loading States
- [ ] Loading indicator saat fetch data
- [ ] Skeleton screens saat initial load (jika ada)
- [ ] Button disabled state saat submit
- [ ] Progress bar animasi smooth

---

## ✅ SECTION 10: FINAL CHECKS

### Performance
- [ ] Page load time < 3 detik
- [ ] No console errors di browser
- [ ] No console warnings yang critical
- [ ] Images dioptimasi (tidak terlalu besar)
- [ ] AJAX requests tidak redundant

### Accessibility
- [ ] Keyboard navigation berfungsi (Tab, Enter, Esc)
- [ ] Screen reader friendly (test dengan screen reader jika bisa)
- [ ] Alt text untuk images
- [ ] ARIA labels untuk interactive elements
- [ ] Focus indicators visible

### Security
- [ ] CSRF token ada di semua form
- [ ] No sensitive data di URL (password, token)
- [ ] File upload restrictions berfungsi
- [ ] SQL injection prevention (Django ORM)
- [ ] XSS prevention (template escaping)

---

## 📝 Bug Report Template

Saat menemukan bug, catat dengan format:

```
**Bug Title:** [Deskripsi singkat]
**URL:** [URL saat bug terjadi]
**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Result:** [Apa yang seharusnya terjadi]
**Actual Result:** [Apa yang benar-benar terjadi]
**Screenshot:** [Attach jika perlu]
**Console Error:** [Copy paste error dari console]
**Browser:** [Chrome 120, Firefox 115, etc.]
**Device:** [Desktop, Mobile, Tablet]
```

---

## 🎉 Testing Complete!

Setelah semua checklist di atas completed, fitur Course Management untuk Instruktor siap untuk production! 🚀

**Total Test Cases:** ~200+ individual checks

**Estimasi Waktu Testing:** 3-4 jam untuk testing menyeluruh

**Priority:**
- 🔴 High: Section 1, 2, 5, 7.1, 7.2, 8.1
- 🟡 Medium: Section 3, 4, 6, 8.2, 8.3, 9
- 🟢 Low: Section 7.3, 8.4, 10

---

**Tips:**
1. Mulai dari High Priority dulu
2. Test dengan real data yang bervariasi
3. Catat semua bug yang ditemukan
4. Test ulang setelah bug fix
5. Minta orang lain untuk test juga (fresh eyes catch more bugs!)

Good luck testing! 🧪✨

