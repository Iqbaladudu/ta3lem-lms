from django import template

from vite import get_config

register = template.Library()


def get_manifest():
    """Load and return the Vite manifest as a dictionary."""
    import json
    from pathlib import Path

    manifest_path = Path(get_config("VITE_MANIFEST_PATH"))
    with manifest_path.open() as f:
        manifest = json.load(f)
    return manifest


@register.inclusion_tag("vite/tags/enable_vite_tags.html")
def enable_vite(entry="index.html"):
    if get_config("VITE_DEV_MODE"):
        # In dev mode, use Vite dev server
        return {
            "vite_js_entry": get_config("VITE_JS_ENTRYPOINT"),
            "vite_css_entry": get_config("VITE_CSS_ENTRYPOINT"),
            "vite_hmr": f"{get_config('VITE_DEV_SERVER_URL')}/@vite/client",
            "js_files": [],
            "css_files": [],
            "django_dev": True,
        }
    else:
        # In production, use manifest
        manifest = get_manifest()
        entry_data = manifest.get(entry, {})
        js_file = entry_data.get("file", "")
        css_files = entry_data.get("css", [])

        # Prefix with dist/ since files are in vite/static/dist/
        js_src = f"dist/{js_file}" if js_file else ""
        css_srcs = [f"dist/{css}" for css in css_files]

        return {
            "vite_js_entry": None,
            "vite_css_entry": None,
            "vite_hmr": None,
            "js_files": [js_src] if js_src else [],
            "css_files": css_srcs,
            "django_dev": False,
        }