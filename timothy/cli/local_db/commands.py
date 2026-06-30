"""
Automates a local development workflow using Testcontainers and Git worktrees.
"""

from dataclasses import dataclass
from functools import partial, update_wrapper
from pathlib import Path
from typing import Callable

import click
from testcontainers.postgres import PostgresContainer
from timothy.cli import cli, stop_event


@dataclass
class Cfg:
    data_loc: Path


def pass_ctx(f: Callable, loc: str):
    @click.pass_context
    def _inject_config(ctx, *args, **kwargs):
        return ctx.invoke(f, ctx.obj[loc], *args, **kwargs)

    return update_wrapper(_inject_config, f)


pass_cfg = partial(pass_ctx, loc="cfg")


@cli.group(help=__doc__)
@click.option(
    "--data-loc",
    type=click.Path(path_type=Path),
    default=None,
    help="Location of the DB data",
)
@click.pass_context
def local_db(ctx, data_loc: Path | None) -> None:
    ctx.ensure_object(dict)
    if data_loc is None:
        data_loc = Path.cwd() / ".db-data"
    ctx.obj["cfg"] = Cfg(data_loc)


@local_db.command(
    help="""
    Dump a remote database to a local volume via `pg_dump`
    so it can be reused by other local-db commands.
    """,
)
@click.argument("conn_str")
@pass_cfg
def dump(cfg: Cfg, conn_str: str) -> None: ...


@local_db.command(
    help="""
    Search Git worktrees for an existing database dump
    that can be mounted into a local container.
    """,
)
@pass_cfg
def copy(cfg: Cfg) -> None: ...


@local_db.command(help="Spin up a Postgres Testcontainer with a local dump mounted.")
@click.option("--version", type=click.IntRange(16, 18), default=17)
@pass_cfg
def up(cfg: Cfg, version) -> None:
    with (
        stop_event() as event,
        PostgresContainer(f"postgres:{version}").with_volume_mapping(
            cfg.data_loc,
            "/docker-entrypoint-initdb.d/seed.sql",
            mode="ro",
        ) as pg,
    ):
        click.echo(f"Postgres is running at: {pg.get_connection_url()}")
        click.echo("Press Ctrl+C to stop.")
        event.wait()
