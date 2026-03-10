from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import List


@dataclass
class CommandResult:
    stdout: str
    stderr: str
    returncode: int


def _resolve_bin(binary: str) -> str:
    found = shutil.which(binary)
    if found:
        return found

    common = [
        f"/usr/bin/{binary}",
        f"/bin/{binary}",
        f"/usr/sbin/{binary}",
        f"/sbin/{binary}",
    ]
    for path in common:
        if shutil.which(path) or os.path.exists(path):
            return path
    return binary


def run_command(command: List[str], timeout: int = 10) -> CommandResult:
    if command:
        command = [_resolve_bin(command[0]), *command[1:]]

    proc = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return CommandResult(stdout=proc.stdout, stderr=proc.stderr, returncode=proc.returncode)
