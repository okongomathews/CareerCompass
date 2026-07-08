from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from users.views import LandingPageView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('assessments/', include('assessments.urls', namespace='assessments')),
    path('recommendations/', include('recommendations.urls', namespace='recommendations')),
    path('ai-coach/', include('ai_coach.urls', namespace='ai_coach')),
    path('analytics/', include('analytics.urls', namespace='analytics')),
    path('coaching/', include('coaching.urls', namespace='coaching')),
    path('', LandingPageView.as_view(), name='landing'),
]

urlpatterns += staticfiles_urlpatterns()
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
