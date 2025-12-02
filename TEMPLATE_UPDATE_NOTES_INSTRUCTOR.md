# Template Update Notes - Instructor Views

> Catatan untuk memperbarui template Django dengan HTMX dan Tailwind CSS
> Tanggal: 2 Desember 2025

## Perubahan Model

Struktur baru:
```
Course → Module → Content → ContentItem (multiple types)
```

Sebelumnya `Content` langsung memiliki satu item (via GenericForeignKey). Sekarang `Content` adalah container yang bisa memiliki banyak `ContentItem` dengan berbagai jenis (text, video, image, file).

---

## Template yang Perlu Diperbarui

### 1. `courses/manage/module/content_list.html`

**Perubahan:**
- Tampilkan `content.title` bukan `content.item.title`
- Loop `content.items.all` untuk menampilkan setiap ContentItem
- Tambah tombol untuk menambah item baru ke Content yang ada

**Contoh Struktur:**
```html
{% for content in module.contents.all %}
<div id="content-{{ content.id }}" class="bg-white rounded-lg shadow p-4 mb-4">
    <div class="flex justify-between items-center border-b pb-2 mb-3">
        <h3 class="font-semibold text-lg">{{ content.title }}</h3>
        <div class="flex gap-2">
            <!-- Tombol tambah item ke content ini -->
            <button hx-get="{% url 'content_item_create' content.id 'text' %}"
                    hx-target="#modal-container"
                    class="text-blue-600 hover:text-blue-800">
                <svg><!-- icon add --></svg>
            </button>
            <!-- Tombol hapus content -->
            <button hx-post="{% url 'module_content_delete' content.id %}"
                    hx-confirm="Hapus content ini beserta semua item?"
                    hx-target="#content-{{ content.id }}"
                    hx-swap="outerHTML"
                    class="text-red-600 hover:text-red-800">
                <svg><!-- icon delete --></svg>
            </button>
        </div>
    </div>
    
    <!-- List ContentItems -->
    <div id="content-items-{{ content.id }}" class="space-y-2">
        {% for item in content.items.all %}
        <div id="content-item-{{ item.id }}" 
             class="flex items-center gap-3 p-2 bg-gray-50 rounded">
            <!-- Icon berdasarkan type -->
            <span class="text-gray-500">
                {% if item.item.content_type == 'text' %}📝
                {% elif item.item.content_type == 'video' %}🎬
                {% elif item.item.content_type == 'image' %}🖼️
                {% elif item.item.content_type == 'file' %}📁
                {% endif %}
            </span>
            <span class="flex-1">{{ item.item.title }}</span>
            <button hx-post="{% url 'content_item_delete' content.id item.id %}"
                    hx-target="#content-item-{{ item.id }}"
                    hx-swap="outerHTML"
                    class="text-red-500 hover:text-red-700">
                ✕
            </button>
        </div>
        {% empty %}
        <p class="text-gray-400 text-sm italic">Belum ada item</p>
        {% endfor %}
    </div>
</div>
{% endfor %}
```

---

### 2. `courses/manage/content/form.html`

**Perubahan:**
- Tambah context `content` dan `module` ke template
- Jika `content` ada, tampilkan sebagai "Tambah item ke content"
- Jika tidak, tampilkan sebagai "Buat content baru"

**Contoh:**
```html
<div class="max-w-2xl mx-auto p-6">
    <h2 class="text-xl font-bold mb-4">
        {% if content %}
            Tambah Item ke "{{ content.title }}"
        {% else %}
            Buat Content Baru
        {% endif %}
    </h2>
    
    <form method="post" enctype="multipart/form-data"
          hx-post="{{ request.path }}"
          hx-target="#form-container"
          class="space-y-4">
        {% csrf_token %}
        
        {% for field in form %}
        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
                {{ field.label }}
            </label>
            {{ field }}
            {% if field.errors %}
            <p class="text-red-500 text-sm mt-1">{{ field.errors.0 }}</p>
            {% endif %}
        </div>
        {% endfor %}
        
        <button type="submit" 
                class="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700">
            Simpan
        </button>
    </form>
</div>
```

---

### 3. `courses/manage/content/item_form.html` (BARU)

**Template baru untuk menambah ContentItem:**
```html
<div class="max-w-2xl mx-auto p-6">
    <h2 class="text-xl font-bold mb-4">
        Tambah {{ model_name|title }} ke "{{ content.title }}"
    </h2>
    
    <form method="post" enctype="multipart/form-data"
          hx-post="{% url 'content_item_create' content.id model_name %}"
          hx-target="#modal-container"
          class="space-y-4">
        {% csrf_token %}
        
        {% for field in form %}
        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
                {{ field.label }}
            </label>
            {{ field }}
        </div>
        {% endfor %}
        
        <div class="flex gap-2">
            <button type="submit" 
                    class="flex-1 bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700">
                Tambah
            </button>
            <button type="button" 
                    onclick="closeModal()"
                    class="px-4 py-2 border rounded hover:bg-gray-100">
                Batal
            </button>
        </div>
    </form>
</div>
```

---

### 4. Dropdown Menu untuk Pilih Tipe Item

**Komponen untuk memilih tipe item yang akan ditambahkan:**
```html
<!-- Dropdown untuk tambah item baru -->
<div class="relative" x-data="{ open: false }">
    <button @click="open = !open" 
            class="flex items-center gap-1 text-blue-600 hover:text-blue-800">
        <svg class="w-5 h-5"><!-- icon plus --></svg>
        Tambah Item
    </button>
    
    <div x-show="open" @click.away="open = false"
         class="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border z-10">
        <a hx-get="{% url 'content_item_create' content.id 'text' %}"
           hx-target="#modal-container"
           class="block px-4 py-2 hover:bg-gray-100">
            📝 Text
        </a>
        <a hx-get="{% url 'content_item_create' content.id 'video' %}"
           hx-target="#modal-container"
           class="block px-4 py-2 hover:bg-gray-100">
            🎬 Video
        </a>
        <a hx-get="{% url 'content_item_create' content.id 'image' %}"
           hx-target="#modal-container"
           class="block px-4 py-2 hover:bg-gray-100">
            🖼️ Image
        </a>
        <a hx-get="{% url 'content_item_create' content.id 'file' %}"
           hx-target="#modal-container"
           class="block px-4 py-2 hover:bg-gray-100">
            📁 File
        </a>
    </div>
</div>
```

---

### 5. Drag & Drop Ordering untuk ContentItems

**HTMX + Sortable.js untuk reorder:**
```html
<div id="content-items-{{ content.id }}" 
     class="space-y-2 sortable-items"
     hx-post="{% url 'content_item_order' %}"
     hx-trigger="end"
     hx-swap="none">
    {% for item in content.items.all %}
    <div class="sortable-item flex items-center gap-3 p-2 bg-gray-50 rounded cursor-move"
         data-id="{{ item.id }}">
        <span class="drag-handle text-gray-400">⋮⋮</span>
        <!-- content item details -->
    </div>
    {% endfor %}
</div>

<script>
// Inisialisasi Sortable.js
new Sortable(document.querySelector('.sortable-items'), {
    handle: '.drag-handle',
    animation: 150,
    onEnd: function(evt) {
        const items = evt.to.querySelectorAll('.sortable-item');
        const order = {};
        items.forEach((item, index) => {
            order[item.dataset.id] = index;
        });
        htmx.ajax('POST', '{% url "content_item_order" %}', {
            values: order
        });
    }
});
</script>
```

---

## URL Patterns Baru

```python
# Untuk instructor content management
path("content/<int:content_id>/item/<model_name>/create/", 
     views.ContentItemCreateView.as_view(), name="content_item_create"),
path("content/<int:content_id>/item/<int:item_id>/delete/", 
     views.ContentItemDeleteView.as_view(), name="content_item_delete"),
path("content-item/order/", 
     views.ContentItemOrderView.as_view(), name="content_item_order"),
```

---

## Checklist Update

- [x] Update `content_list.html` untuk loop ContentItems
- [x] Buat `item_form.html` untuk form tambah item
- [x] Tambah dropdown menu pilih tipe item
- [x] Implementasi drag & drop ordering
- [x] Update delete handlers untuk ContentItem
- [ ] Test HTMX interactions
- [x] Responsive design untuk mobile
