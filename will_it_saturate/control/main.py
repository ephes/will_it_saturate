# AUTOGENERATED! DO NOT EDIT! File to edit: 02_control_server.ipynb (unless otherwise specified).

__all__ = ['read_root', 'create_epoch', 'create_server', 'list_servers', 'machine', 'app', 'servers']

# Cell

import cpuinfo

from pathlib import Path
from pydantic import BaseModel

from fastapi import FastAPI

from ..core import Epoch, BaseServer, get_machine_id

from ..server import (
    FastAPIUvicornServer,
    NginxDockerServer,
    DjangoGunicornWSGIServer,
)


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
def create_server(server: BaseServer):
    print(server)
    global servers
    if server.name not in servers:
        created_server = FastAPIUvicornServer(name=server.name, port=5001)
        created_server.start()
        servers[server.name] = created_server
    return servers[server.name]


@app.get("/servers/")
def list_servers():
    return servers


@app.get("/machine/")
def machine():
    result = {"machine_id": get_machine_id()}
    result.update(cpuinfo.get_cpu_info())
    return result