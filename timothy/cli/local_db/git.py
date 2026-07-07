from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

console = Console()


@dataclass
class Git:
    root: Path
    relative_path: str
    _worktrees: list[Path] | None = None

    @classmethod
    def from_git_setup(cls, path: str | Path) -> Git:
        try:
            root_out = subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"], text=True
            ).strip()
            root = Path(root_out)
            path = Path(path)
            if path.is_absolute():
                path = path.relative_to(root)
            return cls(root, str(path))
        except subprocess.CalledProcessError:
            raise click.Abort()
        except ValueError:
            console.print(f"[red]Path {path} is not inside the git repository.[/red]")
            raise click.Abort()

    @property
    def worktrees(self) -> list[Path]:
        if not self._worktrees:
            try:
                wt_out = subprocess.check_output(
                    ["git", "worktree", "list", "--porcelain"], text=True
                )
            except subprocess.CalledProcessError as e:
                console.print(f"[red]Error discovering git worktrees: {e}[/red]")
                raise click.Abort()

            worktrees = []
            for line in wt_out.splitlines():
                if line.startswith("worktree "):
                    path = Path(line.replace("worktree ", "").strip())
                    data_path = path / self.relative_path
                    if path != self.root and data_path.is_dir():
                        worktrees.append(path)

            if not worktrees:
                console.print(
                    "[yellow]No other git worktrees with local database data found.[/yellow]"
                )
                raise click.Abort()
            self._worktrees = worktrees

        return self._worktrees


@dataclass
class DataLoc:
    source: Path
    target: Path

    @classmethod
    def from_git(cls, current: Git) -> DataLoc:
        table = Table(title="Available Worktrees for DB Cloning")
        table.add_column("#", style="cyan", justify="right")
        table.add_column("Worktree Path", style="magenta")

        for i, wt in enumerate(current.worktrees, 1):
            table.add_row(str(i), str(wt))

        console.print(table)
        choice = click.prompt(
            "Select a worktree to clone from",
            type=click.IntRange(1, len(current.worktrees)),
            default="1",
            show_default=True,
        )

        return cls(
            source=current.worktrees[choice - 1] / current.relative_path,
            target=current.root / current.relative_path,
        )
