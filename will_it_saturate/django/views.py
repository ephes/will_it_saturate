# AUTOGENERATED! DO NOT EDIT! File to edit: 12_views_for_django_server.ipynb (unless otherwise specified).

__all__ = ['IS_ASYNC', 'serve_file_sync', 'serve_file_async', 'set_serve_file_to_async', 'serve_file']

# Cell
from pathlib import Path

from .http import AsyncFileResponse
from .http import MeasuringFileResponse


IS_ASYNC = False

# Cell


async def serve_file_sync(request, base, path, num):
    file_path = Path(base) / path / str(num)
    return MeasuringFileResponse(file_path.open("rb"))


async def serve_file_async(request, base, path, num):
    file_path = Path(base) / path / str(num)
    return AsyncFileResponse(filename=file_path)


serve_file = serve_file_sync


def set_serve_file_to_async():
    global serve_file
    serve_file = serve_file_async