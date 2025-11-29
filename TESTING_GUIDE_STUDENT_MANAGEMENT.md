# Testing Guide - Instructor Student Management

## Prerequisites
- Server Django harus berjalan di `http://localhost:8000`
- Memiliki akun instruktur yang sudah login
- Memiliki minimal 1 kursus dengan siswa yang terdaftar

## Test Cases

### 1. Test Students Overview Page

**URL to Test:** `http://localhost:8000/courses/students/overview/`

**Access Methods:**
1. Dari Dashboard Instruktur: Klik tombol "Kelola Siswa" di header
2. Dari Dashboard Instruktur: Klik pada card statistik "Total Siswa"
3. Direct URL: Navigasi langsung ke URL di atas

**Expected Results:**
✅ Halaman menampilkan header gradient biru-ungu-pink
✅ 4 Statistics cards (Total Siswa, Aktif, Selesai, Rata-rata Progress)
✅ Daftar siswa dengan informasi lengkap
✅ Sidebar dengan statistik per kursus
✅ Tombol "Detail" pada setiap course card berfungsi
✅ Data siswa menampilkan:
   - Avatar dengan inisial
   - Username dan email (jika ada)
   - Waktu akses terakhir
   - Total kursus, kursus aktif, dan selesai
   - Rata-rata progress dengan angka
   - Preview maksimal 3 kursus yang diikuti

**Things to Check:**
- [ ] Statistics cards menampilkan angka yang benar
- [ ] Student list terurut berdasarkan last_accessed (terbaru di atas)
- [ ] Progress bar berfungsi dan menampilkan persentase yang sesuai
- [ ] Responsive di berbagai ukuran layar (mobile, tablet, desktop)
- [ ] Hover effects bekerja dengan baik
- [ ] Link "Kembali ke Dashboard" berfungsi

---

### 2. Test Course Students Page

**URL to Test:** `http://localhost:8000/courses/students/<course_id>/`

**Access Methods:**
1. Dari Students Overview: Klik tombol "Detail" pada course card di sidebar
2. Dari Dashboard Instruktur: Klik tombol "Siswa" pada course card
3. Direct URL dengan course ID yang valid

**Expected Results:**
✅ Header menampilkan judul kursus yang benar
✅ 4 Statistics cards (Total Siswa, Aktif, Selesai, Rata-rata Progress)
✅ Daftar siswa dengan detail progress lengkap
✅ Status badge dengan warna yang tepat (hijau/kuning/abu-abu)
✅ Sidebar menampilkan statistik modul
✅ Tombol "Kembali ke Manajemen Siswa" dan "Analytics" berfungsi

**Things to Check:**
- [ ] Student cards menampilkan informasi yang akurat:
  - Progress percentage benar
  - Modul selesai/total modul benar
  - Konten selesai/total konten benar
  - Sesi belajar terbaru ditampilkan (max 2)
- [ ] Status badge colors:
  - Hijau untuk "Aktif" (enrolled)
  - Kuning untuk "Selesai" (completed)
  - Abu-abu untuk "Ditunda" (paused)
- [ ] Module statistics di sidebar akurat
- [ ] Completion rate per modul dihitung dengan benar
- [ ] Tombol "Lihat Detail Progress" mengarah ke halaman yang benar
- [ ] Responsive design berfungsi baik

---

### 3. Test Navigation Flow

**Test Case 3a: Complete Flow dari Dashboard**
1. Start: Dashboard Instruktur (`/courses/mine/`)
2. Klik "Kelola Siswa" di header
3. Expected: Students Overview page
4. Klik "Detail" pada salah satu course card
5. Expected: Course Students page untuk kursus tersebut
6. Klik "Lihat Detail Progress" pada salah satu siswa
7. Expected: Student Progress Detail page (existing feature)

**Test Case 3b: Alternative Flow**
1. Start: Dashboard Instruktur
2. Klik tombol "Siswa" pada course card
3. Expected: Langsung ke Course Students page
4. Klik "Analytics" di breadcrumb
5. Expected: Course Analytics page
6. Klik detail siswa
7. Expected: Student Progress Detail page

---

### 4. Test Data Accuracy

**Test dengan berbagai kondisi:**

**Case A: Course dengan banyak siswa (10+ siswa)**
- [ ] Semua siswa ditampilkan
- [ ] Statistik dihitung dengan benar
- [ ] Scrolling berfungsi jika perlu
- [ ] Performance tetap baik

**Case B: Course tanpa siswa**
- [ ] Menampilkan empty state yang sesuai
- [ ] Tidak ada error
- [ ] Statistik menunjukkan 0

**Case C: Course dengan siswa di berbagai status**
- [ ] Siswa aktif, selesai, dan ditunda semua ditampilkan
- [ ] Status badge menampilkan warna yang benar
- [ ] Filtering/grouping (jika ada) berfungsi

**Case D: Student dengan progress 0%**
- [ ] Ditampilkan dengan benar
- [ ] Progress bar kosong
- [ ] Tidak ada modul/konten yang ditandai selesai

**Case E: Student dengan progress 100%**
- [ ] Status "Selesai" ditampilkan
- [ ] Semua modul ditandai complete
- [ ] Badge kuning untuk completed

---

### 5. Test Security & Permissions

**Test Case 5a: Unauthorized Access**
1. Logout atau gunakan akun non-instruktur
2. Try to access `/courses/students/overview/`
3. Expected: Redirect to login page

**Test Case 5b: Cross-User Access**
1. Login sebagai Instructor A
2. Try to access `/courses/students/<course_id>/` 
   dengan course_id milik Instructor B
3. Expected: 404 Not Found atau Permission Denied

**Test Case 5c: Student Role Access**
1. Login sebagai student
2. Try to access instructor student management pages
3. Expected: Permission denied atau redirect

---

### 6. Test UI/UX Elements

**Visual Checks:**
- [ ] Gradient colors konsisten dengan theme (biru-ungu-pink)
- [ ] Font sizes dan weights konsisten
- [ ] Icons dari FontAwesome terload dengan baik
- [ ] Rounded corners (rounded-2xl) konsisten
- [ ] Shadows dan hover effects smooth

**Interactive Elements:**
- [ ] Semua tombol clickable dan responsif
- [ ] Hover effects memberikan feedback visual
- [ ] Links memiliki cursor pointer
- [ ] Transitions smooth (duration-200/300)
- [ ] Scale effects pada hover (scale-105) bekerja

**Responsive Design:**
- [ ] Mobile (< 640px): Single column layout
- [ ] Tablet (640px - 1024px): 2 column grid
- [ ] Desktop (> 1024px): 3 column grid dengan sidebar
- [ ] Text tidak overflow
- [ ] Cards tidak terlalu lebar atau sempit

---

### 7. Test Integration with Existing Features

**Integration Point A: Dashboard Instruktur**
- [ ] "Kelola Siswa" button tidak menggangu layout
- [ ] Total Siswa card tetap menampilkan data yang benar
- [ ] Course cards menampilkan tombol "Siswa" dan "Analytics"
- [ ] Semua existing buttons masih berfungsi

**Integration Point B: Analytics Page**
- [ ] Link dari Course Students ke Analytics berfungsi
- [ ] Link dari Analytics ke Student Progress berfungsi
- [ ] Data konsisten antara kedua halaman

**Integration Point C: Student Progress Detail**
- [ ] Breadcrumb/back button berfungsi
- [ ] Data progress siswa konsisten
- [ ] Bisa navigate kembali ke Course Students

---

## Quick Test Checklist

### Minimal Test (Quick Check - 5 menit)
- [ ] Students Overview page loads tanpa error
- [ ] Course Students page loads tanpa error
- [ ] Basic navigation works (klik tombol-tombol utama)
- [ ] Statistics menampilkan angka (tidak 0 semua atau error)
- [ ] No console errors di browser

### Standard Test (Comprehensive - 15 menit)
- [ ] Semua 7 test cases di atas
- [ ] Test di Chrome atau Firefox
- [ ] Test responsive di mobile view
- [ ] Check data accuracy
- [ ] Test security/permissions

### Full Test (Complete - 30 menit)
- [ ] Semua test cases
- [ ] Test di multiple browsers (Chrome, Firefox, Safari)
- [ ] Test di multiple devices (desktop, tablet, mobile)
- [ ] Performance check (load time < 2 detik)
- [ ] Accessibility check (keyboard navigation, screen reader)

---

## Known Issues / Limitations

1. **Performance dengan banyak siswa:**
   - Jika course memiliki 100+ siswa, loading mungkin lambat
   - Consider pagination di versi selanjutnya

2. **Sorting/Filtering:**
   - Saat ini belum ada fitur untuk sort atau filter siswa
   - Bisa ditambahkan di iterasi berikutnya

3. **Export Data:**
   - Belum ada fitur export to CSV/Excel
   - Feature request untuk versi mendatang

---

## Bug Reporting

Jika menemukan bug, catat informasi berikut:
- URL yang diakses
- User role dan permissions
- Browser dan versi
- Screenshot error (jika ada)
- Console error message (jika ada)
- Steps to reproduce
- Expected vs actual behavior

---

## Success Criteria

Fitur dianggap berhasil jika:
✅ Semua halaman load tanpa error
✅ Data ditampilkan dengan akurat
✅ Navigation flow lancar
✅ Security checks passed
✅ UI konsisten dengan design system
✅ Responsive di semua device
✅ No critical bugs

---

**Last Updated:** November 28, 2025
**Version:** 1.0
**Feature:** Instructor Student Management

