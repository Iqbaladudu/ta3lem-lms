import mistune
import re
from django import template
from django.utils import timezone
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def model_name(obj):
    try:
        return obj._meta.model_name
    except AttributeError:
        return None


@register.filter
def mul(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''


@register.filter
def div(value, arg):
    """Divide the value by the argument"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return ''


@register.filter
def mod(value, arg):
    """Return the modulo of the value by the argument"""
    try:
        return float(value) % float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return ''


def extract_video_id(url):
    """Extract video ID from various video platform URL formats"""
    
    # YouTube patterns
    youtube_patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$',  # Direct video ID
    ]
    
    # Vimeo patterns
    vimeo_patterns = [
        r'vimeo\.com\/(?:video\/)?(\d+)',
        r'^(\d+)$',  # Direct video ID for Vimeo
    ]
    
    # Dailymotion patterns
    dailymotion_patterns = [
        r'dailymotion\.com\/video\/([a-zA-Z0-9]+)',
        r'dai\.ly\/([a-zA-Z0-9]+)',
    ]
    
    # Check YouTube
    for pattern in youtube_patterns:
        match = re.search(pattern, url)
        if match:
            return 'youtube', match.group(1)
    
    # Check Vimeo
    for pattern in vimeo_patterns:
        match = re.search(pattern, url)
        if match:
            return 'vimeo', match.group(1)
    
    # Check Dailymotion
    for pattern in dailymotion_patterns:
        match = re.search(pattern, url)
        if match:
            return 'dailymotion', match.group(1)
    
    return None, None


def extract_youtube_id(url):
    """Extract YouTube video ID from various URL formats (backward compatibility)"""
    platform, video_id = extract_video_id(url)
    if platform == 'youtube':
        return video_id
    return None


@register.simple_tag
def video_player(url, height=400, width="100%", min_height="400px", 
                autoplay=False, mute=False, controls=True, loop=False,
                privacy_mode=True, title="Video player", container_class="w-full"):
    """
    Render a customizable video player that supports multiple platforms.
    
    Usage:
        {% load course %}
        {% video_player "https://www.youtube.com/watch?v=VIDEO_ID" %}
        {% video_player "https://vimeo.com/123456789" height=500 %}
        {% video_player video_url autoplay=True mute=True %}
    
    Supported platforms: YouTube, Vimeo, Dailymotion
    """
    platform, video_id = extract_video_id(url)
    
    if not platform or not video_id:
        return mark_safe(f'<div class="text-red-500 p-4 border border-red-300 rounded-lg">Unsupported video URL: {url}</div>')
    
    # Handle width attribute
    width_attr = f'width="{width}"' if isinstance(width, int) else f'style="width: {width};"'
    
    if platform == 'youtube':
        return _render_youtube_player(video_id, height, width_attr, min_height, autoplay, mute, controls, loop, privacy_mode, title, container_class)
    elif platform == 'vimeo':
        return _render_vimeo_player(video_id, height, width_attr, min_height, autoplay, mute, controls, loop, title, container_class)
    elif platform == 'dailymotion':
        return _render_dailymotion_player(video_id, height, width_attr, min_height, autoplay, mute, controls, loop, title, container_class)


def _render_youtube_player(video_id, height, width_attr, min_height, autoplay, mute, controls, loop, privacy_mode, title, container_class):
    """Render YouTube player"""
    domain = "www.youtube-nocookie.com" if privacy_mode else "www.youtube.com"
    embed_url = f"https://{domain}/embed/{video_id}"
    
    params = []
    if autoplay:
        params.append("autoplay=1")
    if mute:
        params.append("mute=1")
    if not controls:
        params.append("controls=0")
    if loop:
        params.append(f"loop=1&playlist={video_id}")
    
    if params:
        embed_url += "?" + "&".join(params)
    
    html = f'''<div class="{container_class}">
    <iframe class="w-full h-full absolute inset-0 rounded-xl" src="{embed_url}" title="{title}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>'''
    
    return mark_safe(html)


def _render_vimeo_player(video_id, height, width_attr, min_height, autoplay, mute, controls, loop, title, container_class):
    """Render Vimeo player"""
    embed_url = f"https://player.vimeo.com/video/{video_id}"
    
    params = []
    if autoplay:
        params.append("autoplay=1")
    if mute:
        params.append("muted=1")
    if loop:
        params.append("loop=1")
    if not controls:
        params.append("controls=0")
    
    if params:
        embed_url += "?" + "&".join(params)
    
    html = f'''<div class="{container_class}">
    <iframe class="w-full h-full absolute inset-0 rounded-xl" src="{embed_url}" title="{title}" frameborder="0" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen></iframe>
</div>'''
    
    return mark_safe(html)


def _render_dailymotion_player(video_id, height, width_attr, min_height, autoplay, mute, controls, loop, title, container_class):
    """Render Dailymotion player"""
    embed_url = f"https://www.dailymotion.com/embed/video/{video_id}"
    
    params = []
    if autoplay:
        params.append("autoplay=1")
    if mute:
        params.append("mute=1")
    if not controls:
        params.append("controls=0")
    if loop:
        params.append("loop=1")
    
    if params:
        embed_url += "?" + "&".join(params)
    
    html = f'''<div class="{container_class}">
    <iframe class="w-full h-full absolute inset-0 rounded-xl" src="{embed_url}" title="{title}" frameborder="0" allow="autoplay; fullscreen" allowfullscreen></iframe>
</div>'''
    
    return mark_safe(html)


@register.simple_tag  
def youtube_player(url, height=400, width="100%", min_height="400px", 
                   autoplay=False, mute=False, controls=True, loop=False,
                   privacy_mode=True, title="YouTube video player",
                   container_class="w-full"):
    """
    Render a customizable YouTube video player (backward compatibility).
    
    Usage:
        {% load course %}
        {% youtube_player "https://www.youtube.com/watch?v=VIDEO_ID" %}
        {% youtube_player video_url height=500 autoplay=True mute=True %}
        {% youtube_player "VIDEO_ID" privacy_mode=False container_class="my-custom-class" %}
    """
    return video_player(url, height, width, min_height, autoplay, mute, controls, loop, privacy_mode, title, container_class)


@register.filter
def video_platform(url):
    """Get the video platform name from URL"""
    platform, _ = extract_video_id(url)
    return platform or 'unknown'


@register.filter  
def video_thumbnail(url, size='default'):
    """Get video thumbnail URL"""
    platform, video_id = extract_video_id(url)
    
    if platform == 'youtube':
        # YouTube thumbnail sizes: default, mqdefault, hqdefault, sddefault, maxresdefault
        return f"https://img.youtube.com/vi/{video_id}/{size}.jpg"
    elif platform == 'vimeo':
        # Vimeo thumbnails require API call, return placeholder
        return f"https://vumbnail.com/{video_id}.jpg"
    elif platform == 'dailymotion':
        # Dailymotion thumbnail
        return f"https://www.dailymotion.com/thumbnail/video/{video_id}"
    
    return None


@register.filter(name='markdown')
def markdown_format(text):
    """Convert Markdown text to HTML with extended features."""
    if not text:
        return ''
    import markdown
    html = markdown.markdown(text, extensions=['extra', 'toc', 'abbr', 'attr_list', 'def_list', 'fenced_code', 'footnotes', 'md_in_html', 'admonition', 'tables', 'codehilite', 'legacy_em', 'legacy_attrs', 'meta', 'nl2br', 'sane_lists', 'smarty', 'mdx_gfm', 'mdx_cite', 'mdx_emdash'])
    return mark_safe(html)


@register.filter
def timeago(value):
    """
    Convert a datetime to a human-readable "time ago" string.
    
    Usage:
        {{ datetime_value|timeago }}
    
    Examples:
        "just now", "5 minutes ago", "2 hours ago", "3 days ago", etc.
    """
    if not value:
        return ''
    
    now = timezone.now()
    
    # Ensure both datetimes are timezone-aware or naive
    if timezone.is_aware(now) and timezone.is_naive(value):
        value = timezone.make_aware(value)
    elif timezone.is_naive(now) and timezone.is_aware(value):
        value = timezone.make_naive(value)
    
    diff = now - value
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return 'just now'
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f'{minutes} minute{"s" if minutes != 1 else ""} ago'
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f'{hours} hour{"s" if hours != 1 else ""} ago'
    elif seconds < 604800:
        days = int(seconds // 86400)
        return f'{days} day{"s" if days != 1 else ""} ago'
    elif seconds < 2592000:
        weeks = int(seconds // 604800)
        return f'{weeks} week{"s" if weeks != 1 else ""} ago'
    elif seconds < 31536000:
        months = int(seconds // 2592000)
        return f'{months} month{"s" if months != 1 else ""} ago'
    else:
        years = int(seconds // 31536000)
        return f'{years} year{"s" if years != 1 else ""} ago'


