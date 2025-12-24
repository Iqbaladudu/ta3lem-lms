from django.contrib.contenttypes.models import ContentType


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