# AUTOGENERATED! DO NOT EDIT! File to edit: 15_django_asgi.ipynb (unless otherwise specified).

__all__ = ['create_app_filesystem', 'create_app_minio', 'create_django_fileresponse_app']

# Cell
# dont_test
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "will_it_saturate.django.settings")

import django

django.setup(set_prefix=False)

from django.conf import settings

from fileresponse.asgi import AsyncFileASGIHandler as DFAsyncFileASGIHandler

from . import urls
from .handlers import AsyncFileASGIHandler
from .handlers import AsyncMinioASGIHandler


def create_app_filesystem():
    urls.urlpatterns = urls.urlpatterns_async_filesystem
    return AsyncFileASGIHandler()


def create_app_minio():
    urls.urlpatterns = urls.urlpatterns_async_minio
    return AsyncMinioASGIHandler()


def create_django_fileresponse_app():
    urls.urlpatterns = urls.urlpatterns_async_minio
    return DFAsyncFileASGIHandler()