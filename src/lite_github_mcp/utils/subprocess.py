from __future__ import annotations

import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CommandResult:
    args: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


def run_command(
    args: Sequence[str],
    *,
    cwd: str | Path | None = None,
    timeout_seconds: float | None = 30.0,
    env: Mapping[str, str] | None = None,
) -> CommandResult:
    completed = subprocess.run(
        list(args),
        cwd=str(cwd) if cwd is not None else None,
        timeout=timeout_seconds,
        env=dict(env) if env is not None else None,
        check=False,
        capture_output=True,
        text=True,
    )
    return CommandResult(
        args=tuple(args),
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
