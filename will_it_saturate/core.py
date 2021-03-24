# AUTOGENERATED! DO NOT EDIT! File to edit: 00_core.ipynb (unless otherwise specified).

__all__ = ['Host', 'calculate_checksum', 'checksum_for_path', 'create_via_filesystem', 'dummy_creator', 'BenchmarkFile',
           'FILE_CREATORS', 'BaseServer', 'BaseClient', 'Epoch', 'convert_size', 'Result', 'BaseRepository',
           'get_macos_machine_id', 'get_linux_machine_id', 'get_machine_id', 'Benchmark']

# Cell

import os
import math
import json
import httpx
import hashlib

import pandas as pd

from pathlib import Path
from urllib.parse import urljoin
from typing import Optional, Callable, Any

from pydantic import BaseModel

# Cell


class Host(BaseModel):
    name: str
    control_port: int = 8001

    @property
    def control_url(self):
        return f"http://{self.name}:{self.control_port}/"

    @property
    def machine(self):
        url = urljoin(self.control_url, "machine")
        r = httpx.get(url)
        r.raise_for_status()
        return r.json()

    def get_or_create_files(self, epoch):
        url = urljoin(self.control_url, "epochs")
        r = httpx.post(url, json=epoch.dict())
        r.raise_for_status()
        return [BenchmarkFile(**file) for file in r.json()["files"]]

    def get_or_create_server(self, server):
        url = urljoin(self.control_url, "servers")
        r = httpx.post(url, json=server.dict())
        r.raise_for_status()
        return server.__class__(**r.json())

# Cell


# class FilesystemCreator(CheckSumMixin, BaseModel):
#     def checksum_for_path(self, path):
#         with path.open("rb") as f:
#             checksum = self.calculate_checksum(f.read())
#         return checksum

#     def __call__(self, path, size):
#         path.parent.mkdir(parents=True, exist_ok=True)
#         if not path.exists():
#             with path.open("wb") as f:
#                 f.write(os.urandom(size))
#         return self.checksum_for_path(path)


def calculate_checksum(content):
    return hashlib.md5(content).hexdigest()


def checksum_for_path(path):
    with path.open("rb") as f:
        checksum = calculate_checksum(f.read())
    return checksum


def create_via_filesystem(path, size):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with path.open("wb") as f:
            f.write(os.urandom(size))
    return checksum_for_path(path)


def dummy_creator(path, size):
    return "dummy"


FILE_CREATORS = {"filesystem": create_via_filesystem, "dummy": dummy_creator}


class BenchmarkFile(BaseModel):
    number: int
    base_path: str
    size: int
    data_root: str = "data"
    hostname: str = "localhost"
    port: int = 8000
    checksum: Optional[str] = None
    creator_name: str = "filesystem"

    @property
    def filesystem_path(self):
        return Path(self.data_root) / self.base_path / str(self.number)

    def get_or_create(self):
        create = FILE_CREATORS.get(self.creator_name)
        self.checksum = create(self.filesystem_path, self.size)

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


class BaseServer(BaseModel):
    protocol: str = "http"
    name: str = "base_server"
    host: str = "localhost"
    port: int = 8000

    def start(self):
        pass

    def stop(self):
        pass

    def is_running(self):
        return False

    def file_to_url(self, file: BenchmarkFile):
        return f"{self.protocol}://{self.host}:{self.port}/{file.path}"

# Cell


class BaseClient(BaseModel):
    name: str = "base_client"

    def verify_checksums(self, epoch, responses):
        checksum_lookup = {}
        for response in responses:
            url = str(response.url)
            checksum_lookup[url] = calculate_checksum(response.content)

        for bf, url in zip(epoch.files, epoch.urls):
            looked_up_checksum = checksum_lookup.get(url, None)
            if bf.checksum != looked_up_checksum:
                print(bf.checksum, looked_up_checksum, url)

            assert bf.checksum == looked_up_checksum

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
    server: str
    client: str
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
            server=server.name,
            client=client.name,
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


# This does not work yet
#     def dict(self):
#         _dict = super().dict()
#         return {
#             **super().dict(),
#             "file_size_h": self.readable_file_size,
#             "bytes_per_second": self.bytes_per_second,
#             "bytes_per_second_h": self.readable_bytes_per_second,
#         }

#     def json(self):
#         return json.dumps(self.dict())

# Cell


class BaseRepository(BaseModel):
    session: Any = None

    def get_result(self, benchmark, result):
        pass

    def add_result(self, benchmark, result):
        pass

# Cell
import cpuinfo
import platform
import subprocess

from pathlib import Path
from functools import cache


def get_macos_machine_id():
    kwargs = {"capture_output": True, "text": True}
    output = subprocess.run(
        [
            "/usr/sbin/system_profiler",
            "SPHardwareDataType",
        ],
        **kwargs,
    )
    machine_id = None
    for line in output.stdout.split("\n"):
        if "Serial Number" in line:
            machine_id = line.split()[-1]
    return machine_id


def get_linux_machine_id():
    machine_id = "linux_dummy"
    with Path("/etc/machine-id").open() as f:
        machine_id = f.read().rstrip()
    return machine_id


@cache
def get_machine_id():
    os = platform.platform().lower().split("-")[0]
    os_lookup = {"macos": get_macos_machine_id, "linux": get_linux_machine_id}
    return os_lookup[os]()


class Benchmark(BaseModel):
    duration: int = 30  # in seconds
    bandwidth: int = int(10 ** 9 / 8)  # in bytes per second
    file_sizes: list[int] = [10 ** 7, 10 ** 6, 10 ** 5]
    epochs: list[Epoch] = []
    file_creator_name: str = "filesystem"
    uname: Optional[Any] = platform.uname()
    cpuinfo: Optional[dict] = cpuinfo.get_cpu_info()
    servers: list[BaseServer] = []
    clients: list[BaseClient] = []
    results: list[Result] = []
    repository: Optional[BaseRepository] = None
    machine_id: str = get_machine_id()

    @property
    def uname_json(self):
        return json.dumps(self.uname)

    def __hash__(self):
        return hash(self.machine_id)

    def __eq__(self, other):
        self.machine_id == other.machine_id

    def create_epoch_from_file_size(self, file_size):
        do_not_copy = {
            "rows",
            "file_sizes",
            "servers",
            "clients",
            "results",
            "repository",
        }
        kwargs = {k: v for k, v in dict(self).items() if k not in do_not_copy}
        epoch = Epoch(file_size=file_size, **kwargs)
        epoch.create_files()
        return epoch

    def create_epochs(self):
        if len(self.epochs) > 0:
            # benchmark rows were already created
            return

        # create a row for each file_size
        for file_size in self.file_sizes:
            self.epochs.append(self.create_epoch_from_file_size(file_size))

    def build_empty_result(self, epoch, server, client):
        return Result(
            server=server.name,
            client=client.name,
            file_size=epoch.file_size,
            elapsed=elapsed,
            complete_size=epoch.complete_size,
            platform=self.uname.machine,
        )

    def test_server_with_client(self, server, client):
        for epoch in self.epochs:
            result = Result.build_empty_result(epoch, server, client)
            if (
                self.repository is not None
                and (
                    already_measured := self.repository.get_result(self, result)
                ).elapsed
                is not None
            ):
                print("already measured: ", already_measured)
                result = already_measured
            else:
                if not server.started:
                    server.start()
                result.elapsed = client.measure(epoch)
                if self.repository is not None:
                    self.repository.add_result(self, result)
                print("measured: ", result)
            self.results.append(result)

    def run(self):
        for server in self.servers:
            # start with servers, because they are more expensive to create
            print(f"server: {server}")
            for client in self.clients:
                self.test_server_with_client(server, client)
            if server.started:
                server.stop()

    def json(self):
        # return super().json(exclude={"rows", "repository"})
        fields = {
            "duration",
            "bandwidth",
            "cpuinfo",
        }
        return super().json(include=fields)

    @property
    def results_frame(self):
        return pd.DataFrame([r.dict_with_properties() for r in self.results])