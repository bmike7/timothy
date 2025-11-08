from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from functools import partial

from .exceptions import already_exists


def run_cmd(*args) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, check=True)


psql = partial(run_cmd, "psql")


@dataclass
class CMD:
    _cmd: str
    _common_args: list[str]
    _db_cluster: DBCluster

    args: list[str] = field(default_factory=list)

    @property
    def cmd(self) -> list[str]:
        return [self._cmd, *self._common_args, *self.args, self._db_cluster.conn_str]


@dataclass
class Step:
    dump: CMD
    restore: CMD

    def clone(self) -> None:
        dump = subprocess.Popen(self.dump.cmd, stdout=subprocess.PIPE)
        subprocess.check_output(self.restore.cmd, stdin=dump.stdout)
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

    def clone_to(self, other: DBCluster) -> None:
        """
        Clones current `DB` as is to other cluster's DB, including
        broken pages.
        """
        other.ensure_db()
        Dump = partial(CMD, "pg_dump", ["--format=plain", "--verbose"], self)
        # not `pg_restore` because `--format=plain`
        Restore = partial(CMD, "psql", ["-X", "--echo-queries"], other)

        clone_steps = [
            Step(
                dump=Dump(
                    [
                        "--section=pre-data",
                        "--clean",
                        "--if-exists",
                        "--create",
                        "--no-acl",
                        "--no-owner",
                    ]
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
