"""
Django settings untuk ta3lem project.

Gunakan environment variable DJANGO_ENV untuk memilih environment:
- development (default)
- staging
- production

Contoh:
    export DJANGO_ENV=production
    python manage.py runserver
"""

import os

# Default ke development jika tidak diset
env = os.environ.get('DJANGO_ENV', 'development')

if env == 'production':
    from .production import *
elif env == 'staging':
    from .staging import *
else:
    from .development import *

