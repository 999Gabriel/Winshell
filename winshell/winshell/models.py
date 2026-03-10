from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ParsedCommand:
    raw: str
    name: str
    args: List[str]
    flags: Dict[str, str | bool]
