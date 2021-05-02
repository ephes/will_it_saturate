# AUTOGENERATED! DO NOT EDIT! File to edit: 16_servers_started_via_docker.ipynb (unless otherwise specified).

__all__ = ['BaseServer', 'FastAPIUvicornServer', 'DjangoGunicornWSGIServer', 'NginxDockerServer']

# Cell

import time
import subprocess

from pydantic import BaseModel

from .files import BenchmarkFile
from .registry import register_model


@register_model
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

    def params(self):
        return {
            "class_name": self.__class__.__name__,
            "parameters": self.dict(),
        }

# Cell

from .registry import register_model


@register_model
class FastAPIUvicornServer(BaseServer):
    name: str = "fastAPI/uvicorn"

    def get_pid(self):
        kwargs = {"shell": True, "capture_output": True, "text": True}
        output = subprocess.run(
            f"ps aux | grep will_it_saturate.fastapi.main:app", **kwargs
        )
        lines = [l for l in output.stdout.split("\n") if len(l) > 0 and "grep" not in l]
        if len(lines) > 0:
            pid = lines[0].split()[1]
            return pid

    @property
    def started(self):
        return self.get_pid() is not None

    def start_server(self):
        subprocess.Popen(
            [
                "uvicorn",
                "--host",
                str(self.host),
                "--port",
                str(self.port),
                "--no-access-log",
                "will_it_saturate.fastapi.main:app",
            ]
        )
        # subprocess.Popen(["uvicorn", "will_it_saturate.fastapi.main:app"])

    def stop_server(self):
        subprocess.check_output(["kill", self.get_pid()])
        time.sleep(1)  # dunno why this is necessary

    def start(self):
        if not self.started:
            self.start_server()

    def stop(self):
        if self.started:
            self.stop_server()

# Cell


@register_model
class DjangoGunicornWSGIServer(BaseServer):
    name: str = "django/gunicorn/wsgi"

    def get_pids(self):
        kwargs = {"shell": True, "capture_output": True, "text": True}
        output = subprocess.run(f"ps aux | grep will_it_saturate.django.wsgi", **kwargs)
        lines = [l for l in output.stdout.split("\n") if len(l) > 0 and "grep" not in l]
        print(len(lines))
        pids = []
        for line in lines:
            pid = line.split()[1]
            pids.append(pid)
        return pids

    @property
    def started(self):
        return len(self.get_pids()) > 0

    def start_server(self):
        subprocess.Popen(
            [
                "gunicorn",
                "--backlog",
                "10000",
                "-w",
                "8",
                "-b" ":8000",
                "will_it_saturate.django.wsgi",
            ]
        )
        time.sleep(2)

    def stop_server(self):
        kill_command = ["kill"]
        kill_command.extend(self.get_pids())
        subprocess.check_output(kill_command)
        time.sleep(1)  # dunno why this is necessary

    def start(self):
        if not self.started:
            self.start_server()

    def stop(self):
        if self.started:
            self.stop_server()

# Cell


class NginxDockerServer(BaseServer):
    name: str = "nginx/docker"
    docker_name: str = "wis-nginx"
    port: int = 8000
    data_root: str = "data"
    subprocess_kwargs = {"shell": True, "capture_output": True, "text": True}

    def write_dockerfile(self):
        dockerfile = f"""
        FROM nginx
        COPY {data_root} /usr/share/nginx/html/{data_root}
        """
        with Path("Dockerfile.nginx").open("w") as f:
            f.write(dockerfile)

    @property
    def docker_id(self):
        output = subprocess.run(
            f"docker ps | grep {self.docker_name}", **self.subprocess_kwargs
        )
        if len(output.stdout) > 0:
            return output.stdout.split()[0]

    @property
    def started(self):
        return self.docker_id is not None

    def stop_container(self, docker_id):
        output = subprocess.run(f"docker kill {docker_id}", **self.subprocess_kwargs)
        print(output.stdout)

    def remove_container(self):
        output = subprocess.run(
            f"docker rm {self.docker_name}", **self.subprocess_kwargs
        )
        print(output.stdout)

    def build_container(self):
        output = subprocess.run(
            f"docker build -f Dockerfile.nginx -t {self.docker_name} .",
            **self.subprocess_kwargs,
        )
        print(output.stdout)

    def start_container(self):
        output = subprocess.run(
            f"docker run --name {self.docker_name} -d -p {self.port}:80 {self.docker_name}",
            **self.subprocess_kwargs,
        )
        print(output.stdout)

    def start_server(self):
        self.remove_container()
        self.build_container()
        self.start_container()

    def stop_server(self):
        if self.started:
            self.stop_container(self.docker_id)
            self.remove_container()
        time.sleep(1)  # dunno why this is necessary

    def start(self):
        if not self.started:
            self.start_server()

    def stop(self):
        if self.started:
            self.stop_server()