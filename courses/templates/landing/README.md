# Landing Page Templates

Folder ini berisi template-template untuk halaman landing Ta3lem LMS yang telah dimodularisasi untuk kemudahan pemeliharaan.

## Struktur File

### File Utama
- **`index.html`** - File utama yang mengatur layout dan menginclude semua section

### Section Components

1. **`hero.html`** - Hero Section
   - Heading utama dan tagline
   - Call-to-action buttons (Daftar/Login)
   - Hero image
   - Gradient background dengan animasi

2. **`stats.html`** - Statistics Section
   - Menampilkan statistik platform:
     - Total kursus tersedia
     - Total siswa terdaftar
     - Total instruktur ahli
   - Menggunakan variabel context: `total_courses`, `total_students`, `total_instructors`

3. **`features.html`** - Features Section
   - Menampilkan fitur-fitur utama platform
   - Grid layout dengan icon dan deskripsi

4. **`how_it_works.html`** - How It Works Section
   - Menjelaskan 3 langkah mudah untuk memulai:
     1. Buat Akun Gratis
     2. Pilih Kursus
     3. Mulai Belajar
   - Menggunakan numbered badges

5. **`featured_courses.html`** - Featured Courses Section
   - Menampilkan kursus-kursus unggulan
   - Conditional rendering: hanya tampil jika `featured_courses` ada
   - Menggunakan variabel context: `featured_courses`
   - Loop untuk menampilkan setiap kursus dengan:
     - Thumbnail/placeholder
     - Judul dan deskripsi
     - Subject badge
     - Informasi instruktur
     - Jumlah modul

6. **`testimonials.html`** - Testimonials Section
   - Menampilkan testimoni dari siswa
   - 3 kolom masonry layout (responsive)
   - Avatar dengan inisial
   - Quote dan informasi pemberi testimoni

7. **`pricing.html`** - Pricing Section
   - Menampilkan paket harga:
     - **Free Tier**: Akses dasar gratis selamanya
     - **Premium Tier**: Akses penuh dengan fitur eksklusif
   - Feature comparison list
   - CTA buttons untuk registrasi/upgrade

8. **`cta.html`** - Call-to-Action Section
   - Final CTA sebelum footer
   - Mendorong user untuk mendaftar
   - Link ke halaman registrasi dan features

## Context Variables yang Dibutuhkan

View yang merender `index.html` harus menyediakan context variables berikut:

```python
{
    'total_courses': int,        # Total jumlah kursus
    'total_students': int,       # Total jumlah siswa
    'total_instructors': int,    # Total jumlah instruktur
    'featured_courses': QuerySet # QuerySet kursus unggulan (optional)
}
```

## Cara Mengedit

### Mengedit Section Tertentu
Untuk mengedit section tertentu, cukup edit file section yang sesuai. Misalnya:
- Untuk mengubah hero text → edit `hero.html`
- Untuk mengubah testimoni → edit `testimonials.html`
- Untuk mengubah harga → edit `pricing.html`

### Menambah Section Baru
1. Buat file baru di folder ini, misal `new_section.html`
2. Tambahkan include di `index.html`:
   ```django
   {% include 'landing/new_section.html' %}
   ```

### Mengubah Urutan Section
Edit urutan `{% include %}` di file `index.html`

## Design System

Semua section menggunakan design system yang konsisten:

### Colors
- **Primary**: `primary-*` classes (Stone palette)
- **Background**: `bg-white`, `bg-primary-50`, `bg-primary-900`
- **Text**: `text-primary-600`, `text-primary-900`

### Spacing
- **Section padding**: `py-24 sm:py-32`
- **Container**: `max-w-7xl mx-auto px-6 lg:px-8`

### Typography
- **Headings**: `text-3xl font-bold tracking-tight sm:text-4xl`
- **Subheadings**: `text-base font-semibold leading-7`
- **Body**: `text-lg leading-8`

### Components
- **Buttons**: Rounded dengan shadow dan hover effects
- **Cards**: Rounded corners dengan subtle shadows
- **Icons**: Font Awesome icons

## Accessibility

Semua section telah dioptimasi untuk accessibility:
- Semantic HTML5 elements (`<section>`, `<article>`, dll)
- ARIA labels (`aria-labelledby`, `aria-hidden`)
- Skip navigation link
- Proper heading hierarchy
- Alt text untuk images

## Responsive Design

Semua section responsive dengan breakpoints:
- **Mobile**: Default
- **Tablet**: `sm:` (640px)
- **Desktop**: `lg:` (1024px)
- **Large Desktop**: `xl:` (1280px)

## Performance

- Lazy loading untuk images: `loading="lazy"`
- Async decoding: `decoding="async"`
- Optimized image sizes
- Minimal inline styles

## Maintenance Tips

1. **Konsistensi**: Gunakan utility classes yang sama di semua section
2. **Reusability**: Jika ada komponen yang digunakan berulang, pertimbangkan untuk membuatnya sebagai partial terpisah
3. **Testing**: Test setiap perubahan di berbagai ukuran layar
4. **Documentation**: Update README ini jika ada perubahan struktur signifikan
