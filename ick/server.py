import subprocess

from msgspec.json import decode, encode

from .api import Hello, HelloResponse  # type: ignore[import-not-found] # FIX ME


class SubprocessServer:
    def __init__(self, rule_config) -> None:  # type: ignore[no-untyped-def] # FIX ME
        pass


class SubprocessManager:
    def __init__(self, command, env, cwd) -> None:  # type: ignore[no-untyped-def] # FIX ME
        self.proc = subprocess.Popen(command, env=env, cwd=cwd)
        self.send_hello()
        self.recv_hello()  # type: ignore[attr-defined] # FIX ME

    def send_hello(self) -> None:
        resp = self.proc.communicate(encode(Hello()))
        decode(resp, HelloResponse)  # type: ignore[call-overload] # FIX ME
