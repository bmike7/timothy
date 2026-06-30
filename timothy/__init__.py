from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from urllib.parse import urlparse

from .exceptions import already_exists


def run_cmd(*args) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, check=True)


psql = partial(run_cmd, "psql")


@dataclass
class CMD:
    _cmd: str
    _common_args: list[str]
    _db_cluster: DBCluster | None = None

    args: list[str] = field(default_factory=list)

    @property
    def cmd(self) -> list[str]:
        parts = [self._cmd, *self._common_args, *self.args]
        if self._db_cluster is not None:
            parts.append(self._db_cluster.conn_str)
        return parts


@dataclass
class Step:
    dump: CMD
    restore: CMD

    def clone(self) -> None:
        dump = subprocess.Popen(self.dump.cmd, stdout=subprocess.PIPE)
        subprocess.run(
            self.restore.cmd,
            stdin=dump.stdout,
            stdout=subprocess.DEVNULL,
            check=True,
        )
        dump.wait()


@dataclass(frozen=True)
class DBCluster:
    username: str
    password: str
    host: str
    db: str
    port: int = 5432

    @property
    def conn_str(self) -> str:
        return (
            f"postgresql://{self.username}:{self.password}"
            f"@{self.host}:{self.port}/{self.db}"
        )

    @property
    def _common_args(self) -> list[str]:
        return ["-h", self.host, "-p", str(self.port), "-U", self.username, "-w"]

    @classmethod
    def from_conn_str(cls, conn_str: str) -> DBCluster:
        parsed = urlparse(conn_str)
        return cls(
            username=parsed.username or "",
            password=parsed.password or "",
            host=parsed.hostname or "localhost",
            db=parsed.path.lstrip("/") or "",
            port=parsed.port or 5432,
        )

    def ensure_db(self, default_db: str = "postgres") -> None:
        conn_params = dict(
            host=self.host,
            port=self.port,
            user=self.username,
            password=self.password,
            dbname=default_db,
        )
        conn_str = " ".join(f"{k}={v}" for k, v in conn_params.items())
        create_query = f"CREATE DATABASE {self.db} template template0;"
        with already_exists():
            psql(conn_str, "-c", create_query)

    def clone_to(self, target: DBCluster | Path) -> None:
        """
        Clones current `DB` as is to target cluster's DB, including
        broken pages.
        """
        Dump = partial(CMD, "pg_dump", ["--format=plain", "--verbose"], self)

        if isinstance(target, Path):
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                target.unlink()
            Restore = partial(CMD, "tee", ["-a", str(target)], None)
        else:
            target.ensure_db()
            # not `pg_restore` because `--format=plain`
            Restore = partial(CMD, "psql", ["-X", "--echo-queries"], target)

        clone_steps = [
            Step(
                dump=Dump(
                    [
                        "--section=pre-data",
                        "--clean",
                        "--if-exists",
                        "--no-acl",
                        "--no-owner",
                    ]
                    + []
                    if isinstance(target, Path)
                    else ["--create"]
                ),
                restore=Restore(),
            ),
            Step(
                # Copy over inconsistent state... (TODO: fix DB)
                dump=Dump(["--section=data", "--disable-triggers"]),
                restore=Restore(),
            ),
            Step(dump=Dump(["--section=post-data"]), restore=Restore()),
        ]
        for step in clone_steps:
            step.clone()
