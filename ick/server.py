import subprocess

from msgspec.json import decode, encode

from .api import Hello, HelloResponse


class SubprocessServer:
    def __init__(self, rule_config):
        pass


class SubprocessManager:
    def __init__(self, command, env, cwd):
        self.proc = subprocess.Popen(command, env=env, cwd=cwd)
        self.send_hello()
        self.recv_hello()

    def send_hello(self):
        resp = self.proc.communicate(encode(Hello()))
        decode(resp, HelloResponse)
