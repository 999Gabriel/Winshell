from __future__ import annotations

import importlib
import pkgutil

from winshell.commands.base import CommandSpec


def load_command_specs() -> list[CommandSpec]:
    specs: list[CommandSpec] = []
    for module_info in pkgutil.iter_modules(__path__):
        if module_info.name == "base":
            continue
        module = importlib.import_module(f"{__name__}.{module_info.name}")
        specs.extend(getattr(module, "COMMANDS", []))
    return specs
