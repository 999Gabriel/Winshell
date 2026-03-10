from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Sequence


@dataclass
class CommandResult:
    stdout: str
    stderr: str
    returncode: int


def run_command(command: Sequence[str], timeout: int = 10) -> CommandResult:
    process = subprocess.run(
        list(command),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return CommandResult(
        stdout=process.stdout.strip(),
        stderr=process.stderr.strip(),
        returncode=process.returncode,
    )
