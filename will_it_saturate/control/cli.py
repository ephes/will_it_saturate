# AUTOGENERATED! DO NOT EDIT! File to edit: 29_control_cli.ipynb (unless otherwise specified).

__all__ = ['run_server']

# Cell

import uvicorn


def run_server():
    print("starting control server")
    uvicorn.run(
        "will_it_saturate.control.main:app",
        host="127.0.0.1",
        port=8001,
        log_level="info",
        reload=True,
    )