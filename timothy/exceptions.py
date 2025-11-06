import subprocess
from contextlib import contextmanager
from typing import Iterator


class AlreadyExists(subprocess.CalledProcessError):
    pass


@contextmanager
def already_exists() -> Iterator:
    try:
        yield
    except subprocess.CalledProcessError as exc:
        if "already exists" in exc.stderr:
            raise AlreadyExists(exc.returncode, exc.cmd)
        raise exc
