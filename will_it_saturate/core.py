# AUTOGENERATED! DO NOT EDIT! File to edit: 00_core.ipynb (unless otherwise specified).

__all__ = ['BenchmarkServer', 'CheckSumMixin', 'BenchmarkClient', 'FilesystemCreator', 'BenchmarkFile', 'BenchmarkRow',
           'convert_size', 'BenchmarkResult', 'Benchmark']

# Cell

import os
import math
import hashlib

import pandas as pd

from pathlib import Path
from typing import Optional, Callable, Any

from pydantic import BaseModel

# Cell


class BenchmarkServer(BaseModel):
    name: str = "base_server"

    def create(self):
        # do nothing
        pass

    def remove(self):
        # do nothing
        pass

# Cell


class CheckSumMixin:
    def calculate_checksum(self, content):
        return hashlib.md5(content).hexdigest()

# Cell


class BenchmarkClient(CheckSumMixin, BaseModel):
    name: str = "base_client"

    def verify_checksums(self, benchmark_files, responses):
        checksum_lookup = {}
        for response in responses:
            url = str(response.url)
            checksum_lookup[url] = self.calculate_checksum(response.content)

        for bf in benchmark_files:
            assert bf.checksum == checksum_lookup.get(bf.url, None)

# Cell


class FilesystemCreator(CheckSumMixin):
    def checksum_for_path(self, path):
        with path.open("rb") as f:
            checksum = self.calculate_checksum(f.read())
        return checksum

    def __call__(self, path, size):
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            with path.open("wb") as f:
                f.write(os.urandom(size))
        return self.checksum_for_path(path)


class BenchmarkFile(BaseModel):
    number: int
    base_path: str
    size: int
    data_root: str = "data"
    hostname: str = "localhost"
    port: int = 8000
    checksum: Optional[str] = None
    creator: Callable = FilesystemCreator()

    @property
    def filesystem_path(self):
        return Path(self.data_root) / self.base_path / str(self.number)

    def get_or_create(self):
        self.checksum = self.creator(self.filesystem_path, self.size)

    @property
    def path(self):
        return f"{self.data_root}/{self.base_path}/{self.number}"

    @property
    def host(self):
        return f"http://{self.hostname}:{self.port}"

    @property
    def url(self):
        return f"{self.host}/{self.path}"

# Cell


class BenchmarkRow(BaseModel):
    file_size: int  # size of a single file
    duration: int = 30  # in seconds
    bandwidth: int = int(10 ** 9 / 8)  # in bytes per second
    files: list[BenchmarkFile] = []
    file_creator: Callable = FilesystemCreator()
    elapsed: Optional[float] = None
    data_root: str = "data"

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

    @property
    def bytes_per_second(self):
        return self.complete_size / self.elapsed

    def create_files(self):
        if len(self.files) > 0:
            return
        for num in range(self.number_of_files):
            benchmark_file = BenchmarkFile(
                number=num,
                base_path=self.base_path,
                size=self.file_size,
                creator=self.file_creator,
                data_root=self.data_root,
            )
            benchmark_file.get_or_create()
            self.files.append(benchmark_file)

# Cell


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return s, size_name[i]


class BenchmarkResult(BaseModel):
    server: str
    client: str
    file_size: int
    elapsed: float
    complete_size: int
    platform: str

    def make_readable(self, size_in_bytes):
        size, unit = convert_size(size_in_bytes)
        return f"{size}{unit}"

    @property
    def readable_file_size(self):
        return self.make_readable(self.file_size)

    @property
    def bytes_per_second(self):
        return self.complete_size / self.elapsed

    @property
    def readable_bytes_per_second(self):
        return self.make_readable(self.bytes_per_second)

    def dict(self):
        _dict = super().dict()
        return {
            **super().dict(),
            "file_size_h": self.readable_file_size,
            "bytes_per_second": self.bytes_per_second,
            "bytes_per_second_h": self.readable_bytes_per_second,
        }

# Cell
import platform


class Benchmark(BaseModel):
    duration: int = 30  # in seconds
    bandwidth: int = int(10 ** 9 / 8)  # in bytes per second
    file_sizes: list[int] = [10 ** 7, 10 ** 6, 10 ** 5]
    rows: list[BenchmarkRow] = []
    file_creator: Callable = FilesystemCreator()
    platform: str = ""
    servers: list[BenchmarkServer] = []
    clients: list[BenchmarkClient] = []
    results: list[BenchmarkResult] = []

    def create_row_from_file_size(self, file_size):
        do_not_copy = {"rows", "file_sizes"}
        kwargs = {k: v for k, v in dict(self).items() if k not in do_not_copy}
        br = BenchmarkRow(file_size=file_size, **kwargs)
        br.create_files()
        return br

    def create_rows(self):
        if len(self.rows) > 0:
            # benchmark rows were already created
            return

        # create a row for each file_size
        for file_size in self.file_sizes:
            self.rows.append(self.create_row_from_file_size(file_size))

    def test_server_with_client(self, server, client):
        for benchmark_row in self.rows:
            elapsed = client.measure(benchmark_row)
            result = BenchmarkResult(
                server=server.name,
                client=client.name,
                file_size=benchmark_row.file_size,
                elapsed=elapsed,
                complete_size=benchmark_row.complete_size,
                platform=self.platform,
            )
            self.results.append(result)

    def collect_information_about_platform(self):
        self.platform = platform.machine()

    def run(self):
        self.collect_information_about_platform()
        for server in self.servers:
            # start with servers, because they are more expensive to create
            server.start()
            for client in self.clients:
                self.test_server_with_client(server, client)
            server.stop()

    @property
    def results_frame(self):
        return pd.DataFrame([r.dict() for r in self.results])