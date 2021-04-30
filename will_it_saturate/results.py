# AUTOGENERATED! DO NOT EDIT! File to edit: 06_results.ipynb (unless otherwise specified).

__all__ = ['convert_size', 'Result']

# Cell

import math

from typing import Optional
from pydantic import BaseModel

from .epochs import Epoch
from .hosts import HostDetails
from .servers import BaseServer
from .clients import BaseClient

# Cell


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return s, size_name[i]


class Result(BaseModel):
    server: BaseServer
    client: BaseClient
    server_details: Optional[HostDetails]
    client_details: Optional[HostDetails]
    file_size: int
    elapsed: Optional[float] = None
    complete_size: int

    def __hash__(self):
        return hash(self.json(exclude={"elapsed"}))

    def __eq__(self, other):
        self_dict, other_dict = self.dict(exclude={"elapsed"}), other.dict(
            exclude={"elapsed"}
        )
        return self_dict == other_dict

    @classmethod
    def build_empty_result(cls, row, server, client):
        return cls(
            server=server,
            client=client,
            file_size=row.file_size,
            complete_size=row.complete_size,
        )

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

    def dict_with_properties(self):
        return {
            **super().dict(),
            "file_size_h": self.readable_file_size,
            "bytes_per_second": self.bytes_per_second,
            "bytes_per_second_h": self.readable_bytes_per_second,
        }

    def dict_for_pandas(self):
        return {
            "server": self.server.name,
            "client": self.client.name,
            "server_host": self.server_details.machine_id,
            "client_host": self.client_details.machine_id,
            "elapsed": self.elapsed,
            "file_size": self.file_size,
            "file_size_h": self.readable_file_size,
            "complete_size": self.complete_size,
            "bytes_per_second": self.bytes_per_second,
            "bytes_per_second_h": self.readable_bytes_per_second,
        }