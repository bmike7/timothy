# Timothy CLI

This CLI contains commands that improve the DX when
working with PostgreSQL DBs.

## 💾 Installation

Install globally with `uv`:

```shell
$ uv tool install git+https://github.com/bmike7/timothy.git
```

Once installed, the `timothy-cli` command is available everywhere.

## ▶️ Usage

Here's what it looks like in practice:

```shell
$ timothy-cli local-db --help
Usage: timothy-cli local-db [OPTIONS] COMMAND [ARGS]...

  Automates a local development workflow using Testcontainers and Git
  worktrees.

Options:
  --data-loc PATH  Location of the DB data
  --help           Show this message and exit.

Commands:
  copy  Search Git worktrees for an existing database dump that can be...
  dump  Dump a remote database to a local volume via `pg_dump` so it can...
  up    Spin up a Postgres Testcontainer with a local dump mounted.
```


## ▶️ Example Usage

Before using this tool, make sure you are allowed to clone the data of
the DB. For example: a small development DB might be fine, a production
DB containing PII not.

```shell
$ timothy-cli local-db dump $(neon connection-string {env} --database-name {name})
$ timothy-cli local-db up
Postgres is running at: postgresql+psycopg2://test:test@localhost:59389/test
Press Ctrl+C to stop.
```

Note the URL `postgresql+psycopg2://test:test@localhost:59389/test`. This sets
up a Docker `testcontainer` for you with the DB dump mounted to it. When you exit the
command (`Ctrl+C`), then the container will be removed as well.

⚠️ Warning: make sure the used `--data-loc` is in your `.gitignore` file to not
accidentally push the DB dump to your remote repo.


## 📜 Scripts

These commands are manual helpers, otherwise they'd be part of the plain
`timothy` library. But sometimes you want to script them instead.
Nothing stops you from pragmatically duct-taping this together with
`subprocess`. That's exactly what I do in one of my private projects.
It might look something like:

```python
import re

from package.admin.cli import cli
from package.admin.utils import ROOT, mocked_apis, watcher
from yoyo import get_backend, read_migrations


@cli.group(help=__doc__)
def local() -> None: ...


@local.command(help="Sets up local development API, DB and mocked external calls")
def setup() -> None:
    data_loc = ROOT / ".db-data" / "seed.sql"

    with (
        mocked_apis(),
        watcher(
            cmd=["timothy-cli", "local-db", f"--data-loc={data_loc}", "up"],
            pattern=re.compile(r"Postgres is running at:\s*(.+)"),
        ) as conn_str
    ):
        print(f"Using DB: {conn_str}")

        print("Ensure the DB schema is up-to-date")
        migrations_path = ROOT / "database" / "single_tenant_migrations"
        backend = get_backend(conn_str.replace("+psycopg2", ""))
        migrations = read_migrations(str(migrations_path))
        with backend.lock():
            backend.apply_migrations(backend.to_apply(migrations))

        ... # start FastAPI app
```

Afterward, I configure a "poe task" and run `poe local` and everything spins
up. This allows me to work offline on my applications.
