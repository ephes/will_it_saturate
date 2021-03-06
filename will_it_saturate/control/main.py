# AUTOGENERATED! DO NOT EDIT! File to edit: 30_control_server.ipynb (unless otherwise specified).

__all__ = ['read_root', 'create_epoch', 'create_server', 'list_servers', 'stop_server', 'host_details', 'measure',
           'app', 'servers']

# Cell

import cpuinfo

from pathlib import Path
from pydantic import BaseModel

from fastapi import FastAPI

from ..epochs import Epoch
from ..hosts import HostDetails

# needed for servers/clients to be registered in CLASS_REGISTRY
from ..servers import BaseServer
from ..clients import BaseClient

from ..registry import ModelParameters


app = FastAPI()

servers = {}


@app.get("/")
def read_root():
    return {"Hello": "World/Control"}


@app.post("/epochs/")
def create_epoch(epoch: Epoch):
    print(epoch)
    epoch.create_files()
    return epoch


@app.post("/servers/")
def create_server(server_params: ModelParameters):
    print(server_params)
    global servers
    server = server_params.to_model()
    if server.name not in servers:
        server.start()
        servers[server.name] = server
    print(servers)
    return server_params


@app.get("/servers/")
def list_servers():
    return servers


@app.post("/server-stop/")
def stop_server(server_params: ModelParameters):
    print(server_params)
    global servers
    server = server_params.to_model()
    stopped = False
    if server.name in servers:
        server.stop()
        del(servers[server.name])
        stopped = True
    print(servers)
    print(stopped)
    return stopped


@app.get("/host-details/")
def host_details() -> HostDetails:
    host_details = HostDetails.build_details_from_localhost()
    return host_details


@app.post("/measure/")
def measure(client_params: ModelParameters, epoch: Epoch):
    benchmark_client = client_params.to_model()
    print("client: ", benchmark_client)
    print("epoch: ", epoch)
    return benchmark_client.measure(epoch)