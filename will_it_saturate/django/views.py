# AUTOGENERATED! DO NOT EDIT! File to edit: 12_django_views.ipynb (unless otherwise specified).

__all__ = ['IS_ASYNC', 'serve_sync_filesystem', 'serve_sync_minio', 'serve_async_filesystem', 'serve_async_minio']

# Cell
from pathlib import Path

from .http import AsyncFileResponse
from .http import MeasuringFileResponse


IS_ASYNC = False

# Cell


def serve_sync_filesystem(request, base, path, num):
    file_path = Path(base) / path / str(num)
    return MeasuringFileResponse(file_path.open("rb"))


def serve_sync_minio(request, base, path, num):
    file_path = Path(base) / path / str(num)
    return MeasuringFileResponse(file_path.open("rb"))


async def serve_async_filesystem(request, base, path, num):
    file_path = Path(base) / path / str(num)
    return AsyncFileResponse(filename=file_path)


async def serve_async_minio(request, base, path, num):
    file_path = Path(base) / path / str(num)
    return AsyncFileResponse(filename=file_path)