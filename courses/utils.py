from django.contrib.contenttypes.models import ContentType

landing_page_features = [
        {
            'icon': 'globe',
            'title': 'Akses Kursus Darimana Saja',
            'description': 'Belajar kapan saja dan dimana saja melalui desktop, tablet, atau smartphone Anda.'
        },
        {
            'icon': 'chart-line',
            'title': 'Tracking Progres',
            'description': 'Pantau kemajuan belajar Anda dengan dashboard analitik yang intuitif dan real-time.'
        },
        {
            'icon': 'certificate',
            'title': 'Sertifikat',
            'description': 'Dapatkan sertifikat resmi yang dapat diverifikasi setelah menyelesaikan kursus.'
        },
        {
            'icon': 'comments',
            'title': 'Forum Diskusi',
            'description': 'Diskusikan materi pelajaran dengan instruktur dan sesama siswa dalam komunitas belajar.'
        },
        {
            'icon': 'book-open',
            'title': 'Materi Berlimpah',
            'description': 'Akses beragam materi pembelajaran mulai dari teks, video, file, dan dokumen pendukung.'
        },
        {
            'icon': 'chalkboard-teacher',
            'title': 'Instruktur Profesional',
            'description': 'Belajar dari instruktur berpengalaman dan ahli di bidangnya masing-masing.'
        }
    ]

landing_page_testimonials = [
    {
        'name': 'Budi Santoso',
        'role': 'Fullstack Developer',
        'content': 'Belajar di Ta3lem sangat menyenangkan. Materinya sangat terstruktur dan mudah diikuti bahkan bagi pemula sekalipun.',
        'initials': 'BS'
    },
    {
        'name': 'Siti Aminah',
        'role': 'Data Scientist',
        'content': 'Platform ini membantu saya meningkatkan keahlian data science saya dengan cepat. Instrukturnya sangat ahli.',
        'initials': 'SA'
    },
    {
        'name': 'Andi Wijaya',
        'role': 'UI/UX Designer',
        'content': 'Sangat merekomendasikan Ta3lem untuk siapa saja yang ingin memulai karir di bidang desain. Kursusnya sangat komprehensif.',
        'initials': 'AW'
    },
    {
        'name': 'Rina Permata',
        'role': 'Digital Marketer',
        'content': 'Berkat Ta3lem, saya bisa memahami konsep digital marketing dengan lebih mendalam dan langsung mempraktikkannya.',
        'initials': 'RP'
    },
    {
        'name': 'Joko Susilo',
        'role': 'Mobile Developer',
        'content': 'Kurikulumnya selalu up-to-date dengan perkembangan teknologi terbaru. Sangat membantu dalam pekerjaan sehari-hari.',
        'initials': 'JS'
    },
    {
        'name': 'Maya Sari',
        'role': 'Product Manager',
        'content': 'Fleksibilitas waktu belajarnya sangat cocok untuk profesional yang sibuk seperti saya. Kualitas videonya juga sangat baik.',
        'initials': 'MS'
    }
]

def invalidate_page_cache(request, url_name):
    """
    Invalidate the cache for the current page.
    """
    from django.core.cache import cache
    cache_key = request.get_full_path()
    cache.delete(cache_key)


def prefetch_content_items(content_items):
    """
    Efficiently prefetch actual items for a list of ContentItem instances.
    
    This solves the N+1 query problem with GenericForeignKey by batching
    item lookups by content type.
    
    Args:
        content_items: Queryset or list of ContentItem instances
        
    Returns:
        dict: {(content_type_id, object_id): item_instance}
    
    Usage:
        content_items = ContentItem.objects.filter(content__module=module)
        items_cache = prefetch_content_items(content_items)
        for ci in content_items:
            actual_item = items_cache.get((ci.content_type_id, ci.object_id))
    """
    from .models import Text, Video, Image, File
    
    # Group object_ids by content_type
    items_by_type = {}
    for ci in content_items:
        key = ci.content_type_id
        items_by_type.setdefault(key, []).append(ci.object_id)
    
    result = {}
    
    # Map content type model names to model classes
    model_map = {
        'text': Text,
        'video': Video,
        'image': Image,
        'file': File
    }
    
    # Fetch all content types we need
    ct_cache = {ct.id: ct for ct in ContentType.objects.filter(id__in=items_by_type.keys())}
    
    for ct_id, obj_ids in items_by_type.items():
        ct = ct_cache.get(ct_id)
        if ct:
            model = model_map.get(ct.model)
            if model:
                for obj in model.objects.filter(id__in=obj_ids):
                    result[(ct_id, obj.id)] = obj
    
    return result


def bulk_prefetch_content_progress(enrollment, course):
    """
    Prefetch all content and module progress for an enrollment at once.
    
    Returns:
        tuple: (content_progress_dict, module_progress_dict)
            - content_progress_dict: {content_id: ContentProgress}
            - module_progress_dict: {module_id: ModuleProgress}
    """
    from .models import ContentProgress, ModuleProgress
    
    content_progress = {
        cp.content_id: cp
        for cp in ContentProgress.objects.filter(enrollment=enrollment)
    }
    
    module_progress = {
        mp.module_id: mp
        for mp in ModuleProgress.objects.filter(enrollment=enrollment)
    }
    
    return content_progress, module_progress


def get_prefetched_modules_data(course, enrollment):
    """
    Get all modules data with prefetched contents and progress.
    
    Returns a list of module data dicts ready for template use.
    """
    from .models import Content, ModuleProgress
    
    # Prefetch all progress at once
    content_progress_map, module_progress_map = bulk_prefetch_content_progress(enrollment, course)
    
    # Get modules with contents
    modules = course.modules.prefetch_related('contents').all()
    
    modules_data = []
    for module in modules:
        module_progress = module_progress_map.get(module.id)
        
        contents = list(module.contents.all())
        total_contents = len(contents)
        completed_contents = sum(
            1 for c in contents
            if content_progress_map.get(c.id) and content_progress_map[c.id].is_completed
        )
        
        contents_with_progress = [
            {
                'content': content,
                'is_completed': (
                    content_progress_map.get(content.id).is_completed
                    if content_progress_map.get(content.id) else False
                )
            }
            for content in contents
        ]
        
        modules_data.append({
            'module': module,
            'progress': module_progress if module_progress else type('obj', (object,), {'is_completed': False})(),
            'total_contents': total_contents,
            'completed_contents': completed_contents,
            'completion_percentage': (completed_contents / total_contents * 100) if total_contents > 0 else 0,
            'contents_with_progress': contents_with_progress,
            'first_content': contents[0] if contents else None
        })
    
    return modules_data