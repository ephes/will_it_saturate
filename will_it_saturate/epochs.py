# AUTOGENERATED! DO NOT EDIT! File to edit: 05_epochs.ipynb (unless otherwise specified).

__all__ = ['Epoch']

# Cell
import math

from pydantic import BaseModel

from .servers import BaseServer
from .clients import BaseClient
from .files import BenchmarkFile, FILE_CREATORS

# Cell


class Epoch(BaseModel):
    file_size: int  # size of a single file
    duration: int = 30  # in seconds
    bandwidth: int = int(10 ** 9 / 8)  # in bytes per second
    files: list[BenchmarkFile] = []
    urls: list[str] = []
    file_creator_name: str = "filesystem"
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
        # FIXME remove elapsed?
        return self.complete_size / elapsed

    def create_files(self):
        if len(self.files) > 0:
            return
        for num in range(self.number_of_files):
            benchmark_file = BenchmarkFile(
                number=num,
                base_path=self.base_path,
                size=self.file_size,
                creator_name=self.file_creator_name,
                data_root=self.data_root,
            )
            benchmark_file.get_or_create()
            self.files.append(benchmark_file)