"""
Automates a local development workflow using Testcontainers and Git worktrees.
"""

import click
from testcontainers.postgres import PostgresContainer
from timothy.cli import cli


@cli.group(help=__doc__)
def local_db() -> None: ...


@local_db.command(
    help="""
    Dump a remote database to a local volume via `pg_dump`
    so it can be reused by other local-db commands.
    """,
)
@click.argument("conn_str")
def dump(conn_str: str) -> None: ...


@local_db.command(
    help="""
    Search Git worktrees for an existing database dump
    that can be mounted into a local container.
    """,
)
def copy() -> None: ...


@local_db.command(help="Spin up a Postgres Testcontainer with a local dump mounted.")
@click.option("--version", type=click.IntRange(16, 18), default=17)
def up(version) -> None: ...
