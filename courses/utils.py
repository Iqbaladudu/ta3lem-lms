def invalidate_page_cache(request, url_name):
    """
    Invalidate the cache for the current page.
    """
    from django.core.cache import cache
    cache_key = request.get_full_path()
    cache.delete(cache_key)