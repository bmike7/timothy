"""
Timothy CLI

Helps you maintain, develop, and test PostgreSQL databases.
Some commands are designed for use with Git worktrees.
"""

import importlib
import pkgutil
from contextlib import suppress
from pathlib import Path

import click


@click.group(help=__doc__)
def cli() -> None: ...


def load_commands() -> None:
    here = Path(__file__).parent
    for mod in pkgutil.walk_packages([str(here)], prefix="timothy.cli."):
        if mod.name.endswith("commands"):
            with suppress(ImportError):
                importlib.import_module(mod.name)


def main() -> None:
    load_commands()
    cli()
