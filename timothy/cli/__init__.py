"""
Timothy CLI

Helps you maintain, develop, and test PostgreSQL databases.
Some commands are designed for use with Git worktrees.
"""

import importlib
import pkgutil
import signal
import threading
from contextlib import contextmanager, suppress
from pathlib import Path
from typing import Iterator

import click


@click.group(help=__doc__)
def cli() -> None: ...


def load_commands() -> None:
    here = Path(__file__).parent
    for mod in pkgutil.walk_packages([str(here)], prefix="timothy.cli."):
        if mod.name.endswith("commands"):
            with suppress(ImportError):
                importlib.import_module(mod.name)


@contextmanager
def stop_event() -> Iterator[threading.Event]:
    event = threading.Event()
    # Gracefully shutdown when CLI is used:
    # - by a user
    old_int = signal.signal(signal.SIGINT, lambda *_: event.set())
    # - by docker, script, CI/CD, ...
    old_term = signal.signal(signal.SIGTERM, lambda *_: event.set())
    try:
        yield event
    finally:
        signal.signal(signal.SIGINT, old_int)
        signal.signal(signal.SIGTERM, old_term)


def main() -> None:
    load_commands()
    cli()
