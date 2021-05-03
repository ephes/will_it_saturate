# AUTOGENERATED! DO NOT EDIT! File to edit: 21_benchmark_client_implementations.ipynb (unless otherwise specified).

__all__ = ['BaseClient', 'HttpxClient', 'counter', 'request', 'AioHttpResponse', 'AioHttpClient', 'WrkClient',
           'counter', 'request']

# Cell

from pydantic import BaseModel

from .registry import register_model
from .files import calculate_checksum


@register_model
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

    def params(self):
        return {
            "class_name": self.__class__.__name__,
            "parameters": self.dict(),
        }

# Cell

import os
import math
import time
import httpx
import asyncio
import aiohttp
import subprocess

from pathlib import Path
from multiprocessing import Pool
from multiprocessing import set_start_method

# from will_it_saturate.old_core import Benchmark
from .servers import BaseServer

# Cell


# just here because of broken nbdev confusing lua with python
counter = 0
request = None


@register_model
class HttpxClient(BaseClient):
    async def measure_server(self, epoch):
        print("measure server")
        print(epoch.urls[0])
        max_connections = min(epoch.number_of_connections, 50)
        limits = httpx.Limits(
            max_keepalive_connections=10, max_connections=max_connections
        )
        timeout = httpx.Timeout(30.0, connect=60.0)
        start = time.perf_counter()
        async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
            responses = await asyncio.gather(*[client.get(url) for url in epoch.urls])
        elapsed = time.perf_counter() - start
        print("done: ", elapsed)
        print("responses status: ", responses[0].status_code)
        return elapsed, responses

    def measure_in_new_process(self, epoch):
        print("new process")
        elapsed, responses = asyncio.run(self.measure_server(epoch))
        self.verify_checksums(epoch, responses)
        return elapsed

    def measure(self, epoch):
        print("measure")
        with Pool(1) as p:
            [result] = p.map(self.measure_in_new_process, [epoch])
        return result




# def run_httpx():
#     byte = 8
#     gigabit = 10 ** 9
#     bandwidth = gigabit / byte
#
#     # file_sizes = [10 ** 7, 10 ** 6]
#     # file_sizes = [10 ** 7, 10 ** 6, 10 ** 5]
#     file_sizes = [10 ** 7]
#
#     benchmark = Benchmark(
#         bandwidth=bandwidth,
#         duration=3,
#         file_sizes=file_sizes,
#         servers=[BenchmarkServer(name="uvicorn")],
#         clients=[HttpxClient(name="httpx")],
#     )
#     benchmark.create_rows()
#     benchmark.run()
#     print(benchmark.results_frame)




# Cell


class AioHttpResponse:
    def __init__(self, url, content):
        self.url = url
        self.content = content


@register_model
class AioHttpClient(BaseClient):
    async def fetch_page(self, session, url):
        async with session.get(url) as response:
            content = await response.read()
            return AioHttpResponse(url, content)

    async def measure_server(self, epoch):
        print("measure server")
        print(epoch.urls[0])
        urls = epoch.urls
        max_connections = min(epoch.number_of_connections, 400)
        conn = aiohttp.TCPConnector(limit=max_connections)
        responses = []
        start = time.perf_counter()
        async with aiohttp.ClientSession(connector=conn) as session:
            tasks = [asyncio.create_task(self.fetch_page(session, url)) for url in urls]
            responses = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start
        return elapsed, responses

    def measure_in_new_process(self, epoch):
        elapsed, responses = asyncio.run(self.measure_server(epoch))
        self.verify_checksums(epoch, responses)
        return elapsed

    def measure(self, epoch):
        with Pool(1) as p:
            [result] = p.map(self.measure_in_new_process, [epoch])
        return result

# Cell


@register_model
class WrkClient(BaseClient):
    connections: int = 20
    duration: int = 20
    threads: int = 1
    host: str = "localhost"
    port: str = "8000"

    def create_urls_string(self, epoch):
        urls = []
        for bf in epoch.files:
            urls.append(f'    {{path = "/{bf.path}"}},')
        return "\n".join(urls)

    def create_lua_script(self, epoch):
        requests_head = "requests = {"
        requests_tail = "}"
        lua_body = """
print(requests[1])

if #requests <= 0 then
  print("multiplerequests: No requests found.")
  os.exit()
end

print("multiplerequests: Found " .. #requests .. " requests")

counter = 1
request = function()
  -- Get the next requests array element
  local request_object = requests[counter]

  -- Increment the counter
  counter = counter + 1

  -- If the counter is longer than the requests array length -> stop and exit
  if counter > #requests then
    wrk.thread:stop()
    os.exit()
  end

  -- Return the request object with the current URL path
  return wrk.format(request_object.method, request_object.path, request_object.headers, request_object.body)
end
        """
        urls = self.create_urls_string(epoch)
        lua = "\n".join([requests_head, urls, requests_tail, lua_body])
        with Path(f"wrk.lua").open("w") as f:
            f.write(lua)

    def run_wrk(self):
        kwargs = {"capture_output": True, "text": True}
        start = time.perf_counter()
        command = [
            "wrk",
            "-c",
            str(self.connections),
            "-t",
            str(self.threads),
            "-s",
            "wrk.lua",
            f"http://{self.host}:{self.port}",
        ]
        print("command: ", " ".join(command))
        output = subprocess.run(
            command,
            **kwargs,
        )
        elapsed = time.perf_counter() - start
        return elapsed

    def measure(self, epoch):
        print("measure? wtf?")
        self.create_lua_script(epoch)
        elapsed = self.run_wrk()
        return elapsed