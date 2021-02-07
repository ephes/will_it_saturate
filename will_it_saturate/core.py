# AUTOGENERATED! DO NOT EDIT! File to edit: 00_core.ipynb (unless otherwise specified).

__all__ = ['md5sum_for_path', 'FilesystemCreator', 'BenchmarkFile', 'BenchmarkRow', 'Benchmark']

# Cell

import os
import math
import hashlib

from pathlib import Path
from typing import Optional, Callable, Any

from pydantic import BaseModel

# Cell


def md5sum_for_path(path):
    with path.open("rb") as f:
        md5sum = hashlib.md5(f.read()).hexdigest()
    return md5sum


class FilesystemCreator:
    def __call__(self, path, size):
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            with path.open("wb") as f:
                f.write(os.urandom(size))
        return md5sum_for_path(path)


class BenchmarkFile(BaseModel):
    number: int
    base_path: str
    size: int
    data_root: str = "data"
    hostname: str = "localhost"
    port: int = 8000
    md5sum: Optional[str] = None
    creator: Callable = FilesystemCreator()

    @property
    def path(self):
        return Path(self.data_root) / self.base_path / str(self.number)

    def get_or_create(self):
        self.md5sum = self.creator(self.path, self.size)

    @property
    def url(self):
        host = f"http://{self.hostname}:{self.port}"
        path = f"files/{self.base_path}/{self.number}"
        return f"{host}/{path}"

# Cell


class BenchmarkRow(BaseModel):
    file_size: int  # size of a single file
    duration: int = 30  # in seconds
    bandwidth: int = int(10 ** 9 / 8)  # in bytes per second
    files: list[BenchmarkFile] = []
    file_creator: Callable = FilesystemCreator()

    def __str__(self):
        return f"size: {self.file_size} duration: {self.duration} bandwidth: {self.bandwidth}"

    @property
    def base_path(self):
        return f"{self.file_size}_{self.duration}_{self.bandwidth}"

    @property
    def complete_size(self):
        return self.duration * self.bandwidth

    @property
    def number_of_files(self):
        return math.ceil(self.complete_size / self.file_size)

    @property
    def number_of_connections(self):
        return math.ceil(self.bandwidth / self.file_size)

    def get_bytes_per_second(self, elapsed):
        return self.complete_size / elapsed

    def create_files(self):
        if len(self.files) > 0:
            return
        for num in range(self.number_of_files):
            benchmark_file = BenchmarkFile(
                number=num,
                base_path=self.base_path,
                size=self.file_size,
                creator=self.file_creator,
            )
            benchmark_file.get_or_create()
            self.files.append(benchmark_file)

# Cell


class Benchmark(BaseModel):
    duration: int = 30  # in seconds
    bandwidth: int = int(10 ** 9 / 8)  # in bytes per second
    rows: list[BenchmarkRow] = []
    file_creator: Callable = FilesystemCreator()

    def create_rows(self, file_sizes):
        if len(self.rows) > 0:
            return
        kwargs = dict(self)
        del kwargs["rows"]
        for file_size in file_sizes:
            benchmark_row = BenchmarkRow(file_size=file_size, **kwargs)
            benchmark_row.create_files()
            self.rows.append(benchmark_row)