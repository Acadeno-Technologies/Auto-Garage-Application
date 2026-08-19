from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

import os

static_dir = settings.STATIC_ROOT if (os.path.exists(settings.STATIC_ROOT) and os.listdir(settings.STATIC_ROOT)) else (settings.BASE_DIR / 'core' / 'static')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': static_dir}),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
] + static(settings.STATIC_URL, document_root=static_dir) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
