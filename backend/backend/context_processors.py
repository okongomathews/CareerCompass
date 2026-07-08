"""
backend/context_processors.py
Provides global template context for CareerCompass Kenya.
"""
from django.conf import settings


def app_context(request):
    """Global context available in all templates."""
    return {
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'CareerCompass Kenya'),
        'SITE_URL':  getattr(settings, 'SITE_URL',  'http://127.0.0.1:8000'),
    }


def static_files_local(request):
    """Kept for backwards compatibility — no longer used in templates."""
    return {}
