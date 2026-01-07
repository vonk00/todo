"""
URL configuration for Nowpad project.
"""
from django.conf import settings
from django.urls import path, include

urlpatterns = [
    path(f'{settings.URL_SECRET_PREFIX}/', include('items.urls')),
]

