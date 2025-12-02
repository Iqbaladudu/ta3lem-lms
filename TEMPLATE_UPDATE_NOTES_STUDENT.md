# Template Update Notes - Student Views

> Catatan untuk memperbarui template Django dengan HTMX dan Tailwind CSS
> Tanggal: 2 Desember 2025

## Perubahan Model

Struktur baru:
```
Course → Module → Content → ContentItem (multiple types)
```

Sekarang satu `Content` bisa memiliki banyak `ContentItem` (text, video, image, file). Student akan melihat semua items dalam satu halaman content.

---

## Template yang Perlu Diperbarui

### 1. `courses/student/course_detail.html`

**Perubahan:**
- Tampilkan `content.title` bukan `content.item.title`
- Bisa tampilkan preview jumlah items per content

**Contoh:**
```html
{% for module_data in modules_data %}
<div class="bg-white rounded-lg shadow mb-4">
    <div class="p-4 border-b flex justify-between items-center cursor-pointer"
         onclick="toggleModule({{ module_data.module.id }})">
        <div class="flex items-center gap-3">
            {% if module_data.progress.is_completed %}
            <span class="text-green-500">✓</span>
            {% else %}
            <span class="text-gray-300">○</span>
            {% endif %}
            <h3 class="font-semibold">{{ module_data.module.title }}</h3>
        </div>
        <span class="text-sm text-gray-500">
            {{ module_data.completed_contents }}/{{ module_data.total_contents }}
        </span>
    </div>
    
    <div id="module-{{ module_data.module.id }}" class="hidden p-4 space-y-2">
        {% for content in module_data.module.contents.all %}
        <a href="{% url 'student_content_view' course.pk module_data.module.pk content.pk %}"
           class="flex items-center gap-3 p-3 rounded hover:bg-gray-50 
                  {% if content.pk in completed_content_ids %}text-green-600{% endif %}">
            
            <!-- Icon berdasarkan jumlah items -->
            <span class="text-gray-400">
                {% if content.items.count > 1 %}📚{% else %}📄{% endif %}
            </span>
            
            <div class="flex-1">
                <p class="font-medium">{{ content.title }}</p>
                <p class="text-xs text-gray-500">
                    {{ content.items.count }} item{% if content.items.count > 1 %}s{% endif %}
                </p>
            </div>
            
            {% if content.pk in completed_content_ids %}
            <span class="text-green-500">✓</span>
            {% endif %}
        </a>
        {% endfor %}
    </div>
</div>
{% endfor %}
```

---

### 2. `courses/student/content_detail.html`

**Perubahan Utama:**
- Loop semua `content.items.all` dan render masing-masing
- Setiap item dirender sesuai tipe (text, video, image, file)
- Semua items ditampilkan dalam satu halaman

**Contoh Struktur:**
```html
<div class="max-w-4xl mx-auto p-6">
    <!-- Header -->
    <div class="mb-6">
        <nav class="text-sm text-gray-500 mb-2">
            <a href="{% url 'student_course_detail' course.pk %}">{{ course.title }}</a>
            <span class="mx-2">›</span>
            <span>{{ module.title }}</span>
        </nav>
        <h1 class="text-2xl font-bold">{{ content.title }}</h1>
    </div>
    
    <!-- Content Items -->
    <div class="space-y-6">
        {% for item in content.items.all %}
        <div class="bg-white rounded-lg shadow p-6">
            {% include item.item.render %}
        </div>
        {% endfor %}
    </div>
    
    <!-- Navigation & Complete Button -->
    <div class="mt-8 flex justify-between items-center">
        {% if previous_content %}
        <a href="{% url 'student_content_view' course.pk module.pk previous_content.pk %}"
           class="flex items-center gap-2 text-blue-600 hover:text-blue-800">
            ← Sebelumnya
        </a>
        {% else %}
        <div></div>
        {% endif %}
        
        {% if not content_progress.is_completed %}
        <button hx-post="{% url 'mark_content_complete' course.pk module.pk content.pk %}"
                hx-target="#completion-status"
                hx-swap="outerHTML"
                class="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700">
            Tandai Selesai ✓
        </button>
        {% else %}
        <span id="completion-status" class="text-green-600 font-medium">
            ✓ Selesai
        </span>
        {% endif %}
        
        {% if next_content %}
        <a href="{% url 'student_content_view' course.pk next_content.module.pk next_content.pk %}"
           class="flex items-center gap-2 text-blue-600 hover:text-blue-800">
            Selanjutnya →
        </a>
        {% else %}
        <div></div>
        {% endif %}
    </div>
</div>
```

---

### 3. `courses/content/*.html` (Render Templates)

Template untuk render setiap tipe item. Lokasi: `courses/templates/courses/content/`

#### `text.html`
```html
<article class="prose max-w-none">
    <h3 class="text-lg font-semibold mb-3">{{ item.title }}</h3>
    <div class="text-gray-700 leading-relaxed">
        {{ item.content|linebreaks }}
    </div>
</article>
```

#### `video.html`
```html
<div class="video-container">
    <h3 class="text-lg font-semibold mb-3">{{ item.title }}</h3>
    
    {% if item.url %}
    <!-- Embedded video (YouTube, Vimeo, etc) -->
    <div class="aspect-video rounded-lg overflow-hidden bg-black">
        {% video item.url as my_video %}
            {% video my_video "large" %}
        {% endvideo %}
    </div>
    {% elif item.file %}
    <!-- Uploaded video file -->
    <video controls class="w-full rounded-lg">
        <source src="{{ item.file.url }}" type="video/mp4">
        Browser tidak mendukung video.
    </video>
    {% endif %}
</div>
```

#### `image.html`
```html
<figure>
    <h3 class="text-lg font-semibold mb-3">{{ item.title }}</h3>
    <img src="{{ item.file.url }}" 
         alt="{{ item.title }}"
         class="w-full rounded-lg shadow"
         loading="lazy">
</figure>
```

#### `file.html`
```html
<div class="file-download">
    <h3 class="text-lg font-semibold mb-3">{{ item.title }}</h3>
    <a href="{{ item.file.url }}" 
       download
       class="inline-flex items-center gap-2 bg-blue-100 text-blue-700 px-4 py-2 rounded-lg hover:bg-blue-200">
        <svg class="w-5 h-5"><!-- download icon --></svg>
        Download {{ item.file.name|slice:"-20:" }}
    </a>
</div>
```

---

### 4. Sidebar dengan Progress (Content View)

**Sidebar untuk navigasi dengan progress indicator:**
```html
<aside class="w-72 bg-gray-50 border-r h-screen overflow-y-auto fixed left-0 top-0 pt-16">
    {% for module_data in modules_data %}
    <div class="border-b">
        <div class="p-3 font-medium bg-gray-100 flex justify-between">
            <span>{{ module_data.module.title }}</span>
            <span class="text-xs text-gray-500">
                {{ module_data.completed_contents }}/{{ module_data.total_contents }}
            </span>
        </div>
        
        <div class="py-1">
            {% for content_data in module_data.contents_with_progress %}
            <a href="{% url 'student_content_view' course.pk module_data.module.pk content_data.content.pk %}"
               class="flex items-center gap-2 px-4 py-2 text-sm hover:bg-gray-100
                      {% if content_data.content.pk == content.pk %}bg-blue-50 text-blue-700{% endif %}">
                
                {% if content_data.is_completed %}
                <span class="text-green-500 text-xs">✓</span>
                {% else %}
                <span class="text-gray-300 text-xs">○</span>
                {% endif %}
                
                <span class="truncate">{{ content_data.content.title }}</span>
                
                {% if content_data.content.items.count > 1 %}
                <span class="text-xs text-gray-400">({{ content_data.content.items.count }})</span>
                {% endif %}
            </a>
            {% endfor %}
        </div>
    </div>
    {% endfor %}
</aside>
```

---

### 5. Progress Bar Component

**Komponen progress bar yang bisa digunakan ulang:**
```html
<!-- Progress Bar -->
<div class="w-full bg-gray-200 rounded-full h-2">
    <div class="bg-green-500 h-2 rounded-full transition-all duration-300"
         style="width: {{ enrollment.progress_percentage }}%">
    </div>
</div>
<p class="text-sm text-gray-600 mt-1">
    {{ enrollment.progress_percentage|floatformat:0 }}% selesai
</p>
```

---

### 6. HTMX untuk Mark Complete

**Button dengan HTMX untuk mark complete tanpa reload:**
```html
<div id="complete-btn-{{ content.pk }}">
    {% if content_progress.is_completed %}
    <div class="flex items-center gap-2 text-green-600">
        <svg class="w-5 h-5"><!-- check icon --></svg>
        <span>Selesai</span>
    </div>
    {% else %}
    <button hx-post="{% url 'mark_content_complete' course.pk module.pk content.pk %}"
            hx-target="#complete-btn-{{ content.pk }}"
            hx-swap="innerHTML"
            class="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 
                   flex items-center gap-2">
        <span>Tandai Selesai</span>
    </button>
    {% endif %}
</div>
```

**Response partial untuk HTMX:**
```html
<!-- courses/student/partials/complete_button.html -->
<div class="flex items-center gap-2 text-green-600">
    <svg class="w-5 h-5"><!-- check icon --></svg>
    <span>Selesai</span>
</div>
```

---

### 7. Auto-scroll ke Item Berikutnya

**JavaScript untuk smooth scroll antar items:**
```html
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Scroll ke item yang belum selesai
    const incompleteItem = document.querySelector('[data-completed="false"]');
    if (incompleteItem) {
        incompleteItem.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
});

// Setelah mark complete, scroll ke item berikutnya
document.body.addEventListener('htmx:afterSwap', function(evt) {
    if (evt.detail.target.id.startsWith('complete-btn-')) {
        const nextItem = evt.detail.target.closest('.content-item')?.nextElementSibling;
        if (nextItem) {
            nextItem.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
});
</script>
```

---

## View Context yang Perlu Diperbarui

Di `StudentContentView`, pastikan context menyertakan items:

```python
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    content = self.object
    
    # Items sudah bisa diakses via content.items.all di template
    # Tapi untuk optimasi, bisa prefetch:
    context['content_items'] = content.items.select_related('content_type').all()
    
    # ... rest of context
    return context
```

---

## Checklist Update

- [ ] Update `course_detail.html` - tampilkan content.title
- [ ] Update `content_detail.html` - loop content.items.all
- [ ] Buat/update render templates (text.html, video.html, image.html, file.html)
- [ ] Update sidebar navigation
- [ ] Implementasi HTMX mark complete
- [ ] Test progress tracking
- [ ] Responsive design untuk mobile
- [ ] Loading states untuk HTMX requests
- [ ] Error handling untuk failed requests
