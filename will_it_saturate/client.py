# AUTOGENERATED! DO NOT EDIT! File to edit: 02_benchmark_clients.ipynb (unless otherwise specified).

__all__ = ['BaseClient', 'HttpxClient', 'HttpxClient', 'AioHttpResponse', 'AioHttpClient']

# Cell

import os
import math
import time
import httpx
import asyncio
import aiohttp

from pathlib import Path

from .core import Benchmark

# Cell


class BaseClient:
    def __init__(self, benchmark, server, client):
        self.benchmark = benchmark
        self.server = server
        self.client = client

    def check_md5sums(self, benchmark_files, responses):
        md5_lookup = {}
        for response in responses:
            url = str(response.url)
            md5_lookup[url] = hashlib.md5(response.content).hexdigest()

        for bf in benchmark_files:
            assert bf.md5sum == md5_lookup.get(bf.url, "wrong")

    def show_results(self):
        print(
            f"Filesize  Transferred for server {self.server} with client {self.client}"
        )
        for row in self.benchmark.rows:
            file_size, file_unit = convert_size(row.file_size)
            transferred_per_second, transferred_unit = convert_size(
                row.bytes_per_second
            )
            file_string = f"{file_size}{file_unit}"
            transferred_string = f"{transferred_per_second}{transferred_unit}/s"
            print(f"{file_string} {transferred_string:>11s}")

# Cell

from .core import BenchmarkClient


class HttpxClient(BenchmarkClient):
    async def measure_benchmark_row(self, br):
        urls = [bf.url for bf in br.files]
        # httpx breaks on more than 100 parallel connections
        max_connections = min(br.number_of_connections, 100)
        limits = httpx.Limits(
            max_keepalive_connections=5, max_connections=max_connections
        )
        start = time.perf_counter()
        async with httpx.AsyncClient(limits=limits) as client:
            responses = await asyncio.gather(*[client.get(url) for url in urls])
        elapsed = time.perf_counter() - start
        self.verify_checksums(br.files, responses)
        br.elapsed = elapsed

    def measure_benchmark_row(self, br):


# Cell

from .core import BenchmarkClient


class HttpxClient(BenchmarkClient):
    async def measure_benchmark_row(self, br):
        urls = [bf.url for bf in br.files]
        # httpx breaks on more than 100 parallel connections
        max_connections = min(br.number_of_connections, 100)
        limits = httpx.Limits(
            max_keepalive_connections=5, max_connections=max_connections
        )
        start = time.perf_counter()
        async with httpx.AsyncClient(limits=limits) as client:
            responses = await asyncio.gather(*[client.get(url) for url in urls])
        elapsed = time.perf_counter() - start
        self._md5sums(br.files, responses)
        return elapsed

# Cell


class AioHttpResponse:
    def __init__(self, url, content):
        self.url = url
        self.content = content


class AioHttpClient(BaseClient):
    async def fetch_page(self, session, url):
        async with session.get(url) as response:
            content = await response.read()
            return AioHttpResponse(url, content)

    async def measure_benchmark_row(self, br):
        urls = [bf.url for bf in br.files]
        max_connections = min(br.number_of_connections, 200)
        # max_connections = br.number_of_connections
        conn = aiohttp.TCPConnector(limit=max_connections)
        responses = []
        start = time.perf_counter()
        async with aiohttp.ClientSession(connector=conn) as session:
            tasks = [asyncio.create_task(self.fetch_page(session, url)) for url in urls]
            responses = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start
        self.responses = responses
        self.check_md5sums(br.files, responses)
        br.elapsed = elapsed

    async def run(self):
        for br in self.benchmark.rows:
            await self.measure_benchmark_row(br)