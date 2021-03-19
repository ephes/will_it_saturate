# AUTOGENERATED! DO NOT EDIT! File to edit: 02_control_server.ipynb (unless otherwise specified).

__all__ = ['read_root', 'create_epoch', 'create_server', 'list_servers', 'app', 'servers']

# Cell

from pathlib import Path
from pydantic import BaseModel

from fastapi import FastAPI

from ..core import Epoch, FilesystemCreator, BaseServer

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
    epoch.file_creator = FilesystemCreator()
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