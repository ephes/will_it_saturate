# AUTOGENERATED! DO NOT EDIT! File to edit: 02_benchmark_clients.ipynb (unless otherwise specified).

__all__ = ['HttpxClient', 'run_httpx']

# Cell

import os
import math
import time
import httpx
import asyncio
import aiohttp

from pathlib import Path
from multiprocessing import Pool
from multiprocessing import set_start_method

from .core import Benchmark, BenchmarkServer

try:
    set_start_method("fork")
except RuntimeError:
    pass

# Cell


from .core import BenchmarkClient


class HttpxClient(BenchmarkClient):
    async def measure_server(self, benchmark_row):
        print("measure server")
        urls = [bf.url for bf in benchmark_row.files]
        print(urls[0])
        max_connections = min(benchmark_row.number_of_connections, 100)
        limits = httpx.Limits(
            max_keepalive_connections=5, max_connections=max_connections
        )
        start = time.perf_counter()
        async with httpx.AsyncClient(limits=limits) as client:
            responses = await asyncio.gather(*[client.get(url) for url in urls])
        elapsed = time.perf_counter() - start
        print("done")
        return elapsed, responses

    def measure_in_new_process(self, benchmark_row):
        print("new process")
        elapsed, responses = asyncio.run(self.measure_server(benchmark_row))
        self.verify_checksums(benchmark_row.files, responses)
        return elapsed

    def measure(self, benchmark_row):
        print("measure")
        with Pool(1) as p:
            [result] = p.map(self.measure_in_new_process, [benchmark_row])
        return result


def run_httpx():
    byte = 8
    gigabit = 10 ** 9
    bandwidth = gigabit / byte

    # file_sizes = [10 ** 7, 10 ** 6]
    # file_sizes = [10 ** 7, 10 ** 6, 10 ** 5]
    file_sizes = [10 ** 7]

    benchmark = Benchmark(
        bandwidth=bandwidth,
        duration=3,
        file_sizes=file_sizes,
        servers=[BenchmarkServer(name="uvicorn")],
        clients=[HttpxClient(name="httpx")],
    )
    benchmark.create_rows()
    benchmark.run()
    print(benchmark.results_frame)

#    client = HttpxClient()
#    result = client.measure(benchmark.rows[0])
#    print(result)