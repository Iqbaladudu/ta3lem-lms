import re
from django import template
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


def extract_youtube_id(url):
    """Extract YouTube video ID from various URL formats"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$',  # Direct video ID
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


@register.simple_tag
def youtube_player(url, height=400, width="100%", min_height="400px", 
                   autoplay=False, mute=False, controls=True, loop=False,
                   privacy_mode=True, title="YouTube video player",
                   container_class="w-full"):
    """
    Render a customizable YouTube video player.
    
    Usage:
        {% load course %}
        {% youtube_player "https://www.youtube.com/watch?v=VIDEO_ID" %}
        {% youtube_player video_url height=500 autoplay=True mute=True %}
        {% youtube_player "VIDEO_ID" privacy_mode=False container_class="my-custom-class" %}
    
    Parameters:
        url: YouTube URL or video ID
        height: iframe height in pixels (default: 400)
        width: iframe width (default: "100%")
        min_height: container minimum height (default: "400px")
        autoplay: enable autoplay (default: False)
        mute: mute video (default: False)
        controls: show controls (default: True)
        loop: loop video (default: False)
        privacy_mode: use youtube-nocookie.com (default: True)
        title: iframe title for accessibility (default: "YouTube video player")
        container_class: CSS class for container div (default: "w-full")
    """
    video_id = extract_youtube_id(url)
    if not video_id:
        return mark_safe('<div class="text-red-500">Invalid YouTube URL</div>')
    
    # Build embed URL
    domain = "www.youtube-nocookie.com" if privacy_mode else "www.youtube.com"
    embed_url = f"https://{domain}/embed/{video_id}"
    
    # Build query parameters
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
    
    # Handle width
    width_attr = f'width="{width}"' if isinstance(width, int) else f'style="width: {width};"'
    
    html = f'''<div class="{container_class}" style="min-height: {min_height};">
    <iframe class="w-full" height="{height}" {width_attr} src="{embed_url}" title="{title}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>'''
    
    return mark_safe(html)

