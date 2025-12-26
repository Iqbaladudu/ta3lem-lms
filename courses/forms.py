from django.forms.models import inlineformset_factory
from django import forms
from embed_video.fields import EmbedVideoField

from .models import Course, Module, Video

class CourseForm(forms.ModelForm):
    """Enhanced form for course management with status, enrollment, and waitlist settings"""
    
    class Meta:
        model = Course
        fields = [
            'subject', 'title', 'slug', 'overview',
            'pricing_type', 'is_free', 'price', 'currency',
            'status', 'enrollment_type', 'max_capacity', 'waitlist_enabled',
            'difficulty_level', 'estimated_hours', 'certificate_enabled'
        ]
        widgets = {
            'subject': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition'
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition',
                'placeholder': 'Contoh: Pemrograman Python untuk Pemula'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition',
                'placeholder': 'python-pemula (akan dibuat otomatis dari judul)'
            }),
            'overview': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition resize-y',
                'rows': 5,
                'placeholder': 'Deskripsi singkat tentang kursus ini, apa yang akan dipelajari siswa, dan manfaat yang akan didapat...'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition'
            }),
            'enrollment_type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition'
            }),
            'max_capacity': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition',
                'placeholder': 'Kosongkan untuk tidak ada batas',
                'min': '1'
            }),
            'waitlist_enabled': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2'
            }),
            'difficulty_level': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition'
            }),
            'estimated_hours': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition',
                'placeholder': 'Estimasi jam pembelajaran',
                'min': '1'
            }),
            'certificate_enabled': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2'
            }),
            'is_free': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition',
                'placeholder': 'Harga kursus',
                'min': '0',
                'step': '0.01'
            }),
            'currency': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition'
            }),
            'pricing_type': forms.RadioSelect(attrs={
                'class': 'pricing-type-radio'
            }),
        }
        help_texts = {
            'slug': 'URL unik untuk kursus. Akan dibuat otomatis dari judul jika dikosongkan.',
            'pricing_type': 'Pilih bagaimana siswa dapat mengakses kursus ini.',
            'is_free': 'Centang jika kursus ini gratis. Jika tidak, atur harga di bawah.',
            'price': 'Harga kursus (kosongkan jika gratis)',
            'currency': 'Mata uang untuk harga kursus',
            'status': 'Draft: Belum terlihat publik | Published: Tersedia untuk pendaftaran | Archived: Tidak aktif',
            'enrollment_type': 'Open: Pendaftaran bebas | Approval: Perlu persetujuan | Restricted: Akses terbatas',
            'max_capacity': 'Batas maksimal siswa yang dapat mendaftar. Kosongkan untuk tidak ada batas.',
            'waitlist_enabled': 'Aktifkan daftar tunggu ketika kapasitas penuh',
            'difficulty_level': 'Level kesulitan untuk membantu siswa memilih kursus yang sesuai',
            'estimated_hours': 'Perkiraan total jam belajar untuk menyelesaikan kursus',
            'certificate_enabled': 'Berikan sertifikat kepada siswa yang menyelesaikan kursus'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Customize field labels with Indonesian terms
        self.fields['subject'].label = "Kategori Kursus"
        self.fields['title'].label = "Judul Kursus"
        self.fields['slug'].label = "URL Slug"
        self.fields['overview'].label = "Deskripsi Kursus"
        self.fields['pricing_type'].label = "Tipe Harga"
        self.fields['is_free'].label = "Kursus Gratis"
        self.fields['price'].label = "Harga"
        self.fields['currency'].label = "Mata Uang"
        self.fields['status'].label = "Status Publikasi"
        self.fields['enrollment_type'].label = "Tipe Pendaftaran"
        self.fields['max_capacity'].label = "Kapasitas Maksimal"
        self.fields['waitlist_enabled'].label = "Aktifkan Daftar Tunggu"
        self.fields['difficulty_level'].label = "Level Kesulitan"
        self.fields['estimated_hours'].label = "Estimasi Jam Belajar"
        self.fields['certificate_enabled'].label = "Sertifikat Tersedia"
        
        # Make slug field optional and auto-generate from title
        self.fields['slug'].required = False
        
        # Make currency not required - it will use default when is_free=True
        self.fields['currency'].required = False
    
    def clean_max_capacity(self):
        max_capacity = self.cleaned_data.get('max_capacity')
        if max_capacity is not None and max_capacity < 1:
            raise forms.ValidationError('Kapasitas maksimal harus lebih dari 0.')
        return max_capacity
    
    def clean_estimated_hours(self):
        estimated_hours = self.cleaned_data.get('estimated_hours')
        if estimated_hours is not None and estimated_hours < 1:
            raise forms.ValidationError('Estimasi jam belajar harus lebih dari 0.')
        return estimated_hours
    
    def clean(self):
        cleaned_data = super().clean()
        max_capacity = cleaned_data.get('max_capacity')
        waitlist_enabled = cleaned_data.get('waitlist_enabled')
        pricing_type = cleaned_data.get('pricing_type')
        price = cleaned_data.get('price')
        currency = cleaned_data.get('currency')
        
        # If waitlist is enabled but no max capacity is set, show warning
        if waitlist_enabled and not max_capacity:
            self.add_error('waitlist_enabled', 
                'Daftar tunggu hanya dapat diaktifkan jika ada batas kapasitas maksimal.')
        
        # Sync is_free based on pricing_type
        is_free = pricing_type in ['free', 'subscription_only']
        cleaned_data['is_free'] = is_free
        
        # Handle pricing logic based on pricing_type:
        # - 'free': No price needed
        # - 'subscription_only': No price needed (access via subscription only)
        # - 'one_time': Price required
        # - 'both': Price required (subscription OR one-time purchase)
        
        needs_price = pricing_type in ['one_time', 'both']
        
        if is_free or pricing_type == 'subscription_only':
            # Clear price for free and subscription-only courses
            cleaned_data['price'] = None
            # Ensure currency has a default value
            if not currency:
                cleaned_data['currency'] = 'IDR'
        elif needs_price:
            # Course with one-time purchase option must have valid price
            if price is None or price <= 0:
                self.add_error('price', 
                    'Harga harus diisi dan lebih dari 0 untuk kursus berbayar.')
            # Must have currency
            if not currency:
                self.add_error('currency',
                    'Mata uang harus dipilih untuk kursus berbayar.')
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Sync is_free based on pricing_type
        # - 'free': is_free=True, price=None
        # - 'subscription_only': is_free=True, price=None (access via subscription)
        # - 'one_time': is_free=False, price required
        # - 'both': is_free=False, price required
        if instance.pricing_type in ['free', 'subscription_only']:
            instance.is_free = True
            instance.price = None
        else:
            instance.is_free = False
        
        # Auto-generate slug from title if not provided
        if not instance.slug and instance.title:
            from django.utils.text import slugify
            import re
            # Create basic slug from title
            base_slug = slugify(instance.title)
            # Make it more readable by replacing common patterns
            base_slug = re.sub(r'-+', '-', base_slug).strip('-')
            
            # Ensure uniqueness
            slug = base_slug
            counter = 1
            while Course.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            instance.slug = slug
        
        if commit:
            instance.save()
        return instance

class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition',
                'placeholder': 'Contoh: Pengenalan Python, Advanced JavaScript, dll'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition resize-none',
                'rows': 4,
                'placeholder': 'Jelaskan apa yang akan dipelajari di modul ini...'
            })
        }

class VideoForm(forms.ModelForm):
    """Enhanced form for video content with better UX"""
    
    class Meta:
        model = Video
        fields = [
            'title', 'url', 'file', 'duration', 'video_platform', 
            'transcript', 'captions_enabled', 'auto_play', 'minimum_watch_percentage'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition',
                'placeholder': 'Judul video (contoh: Pengenalan Variabel Python)'
            }),
            'url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition',
                'placeholder': 'https://www.youtube.com/watch?v=... atau https://vimeo.com/...'
            }),
            'file': forms.ClearableFileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition',
                'accept': 'video/*'
            }),
            'duration': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition',
                'placeholder': 'Durasi dalam detik (opsional)',
                'min': '1'
            }),
            'video_platform': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition'
            }),
            'transcript': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition resize-y',
                'rows': 6,
                'placeholder': 'Transkrip lengkap video untuk aksesibilitas...'
            }),
            'captions_enabled': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2'
            }),
            'auto_play': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2'
            }),
            'minimum_watch_percentage': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition',
                'min': '1',
                'max': '100',
                'value': '80'
            }),
        }
        help_texts = {
            'url': 'Masukkan URL video dari YouTube, Vimeo, atau Dailymotion. Platform akan terdeteksi otomatis.',
            'file': 'Atau upload file video langsung (MP4 direkomendasikan)',
            'duration': 'Durasi video dalam detik. Akan membantu siswa memperkirakan waktu belajar.',
            'transcript': 'Transkrip teks untuk aksesibilitas dan SEO. Sangat direkomendasikan.',
            'captions_enabled': 'Centang jika video memiliki subtitel atau caption',
            'auto_play': 'Video akan diputar otomatis ketika halaman dimuat (tidak direkomendasikan)',
            'minimum_watch_percentage': 'Persentase minimal video yang harus ditonton untuk dianggap selesai'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add enhanced field descriptions
        self.fields['url'].label = "URL Video (YouTube/Vimeo/Dailymotion)"
        self.fields['file'].label = "Upload File Video"
        self.fields['video_platform'].label = "Platform Video"
        self.fields['transcript'].label = "Transkrip Video"
        self.fields['captions_enabled'].label = "Subtitel Tersedia"
        self.fields['auto_play'].label = "Putar Otomatis"
        self.fields['minimum_watch_percentage'].label = "Minimum Persentase Tonton (%)"
    
    def clean(self):
        cleaned_data = super().clean()
        url = cleaned_data.get('url')
        file = cleaned_data.get('file')
        
        if not url and not file:
            raise forms.ValidationError('Harap masukkan URL video atau upload file video.')
        
        if url and file:
            raise forms.ValidationError('Pilih salah satu: URL video atau upload file, tidak keduanya.')
        
        # Validate minimum watch percentage
        min_percentage = cleaned_data.get('minimum_watch_percentage')
        if min_percentage and (min_percentage < 1 or min_percentage > 100):
            raise forms.ValidationError('Persentase minimum harus antara 1-100%.')
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Auto-detect platform if URL is provided
        if instance.url and not instance.video_platform:
            from .templatetags.course import extract_video_id
            platform, video_id = extract_video_id(str(instance.url))
            if platform:
                instance.video_platform = platform
        elif instance.file and not instance.video_platform:
            instance.video_platform = 'uploaded'
        
        if commit:
            instance.save()
        return instance

ModuleFormSets = inlineformset_factory(
    Course,
    Module,
    form=ModuleForm,
    extra=2,
    can_delete=True,
    can_delete_extra=True
)

