# AUTOGENERATED! DO NOT EDIT! File to edit: 31_control_client.ipynb (unless otherwise specified).

__all__ = ['ControlClient']

# Cell

import httpx

from pydantic import BaseModel
from urllib.parse import urljoin

from ..files import BenchmarkFile
from ..hosts import Host, HostDetails
from ..registry import ModelParameters


class ControlClient(BaseModel):
    host: Host

    @property
    def base_url(self):
        return f"http://{self.host.name}:{self.host.port}/"

    def get_host_details(self):
        url = urljoin(self.base_url, "host-details")
        r = httpx.get(url)
        r.raise_for_status()
        return HostDetails(**r.json())

    def get_or_create_files(self, epoch):
        url = urljoin(self.base_url, "epochs")
        r = httpx.post(url, json=epoch.dict())
        r.raise_for_status()
        return [BenchmarkFile(**file) for file in r.json()["files"]]

    def get_or_create_server(self, server):
        url = urljoin(self.base_url, "servers")
        r = httpx.post(url, json=server.params())
        r.raise_for_status()
        return ModelParameters(**r.json()).to_model()

    def stop_server(self, server):
        url = urljoin(self.base_url, "server-stop")
        r = httpx.post(url, json=server.params())
        r.raise_for_status()
        return r.json()

    def measure(self, client, epoch):
        url = urljoin(self.base_url, "measure")
        data = {"client_params": client.params(), "epoch": epoch.dict()}
        r = httpx.post(url, json=data, timeout=None)
        r.raise_for_status()
        return r.json()