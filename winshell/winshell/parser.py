import shlex
from winshell.models import ParsedCommand


class CommandParser:
    def parse(self, raw: str) -> ParsedCommand:
        text = (raw or "").strip()
        if not text:
            return ParsedCommand(raw=raw, name="", args=[], flags={})

        tokens = shlex.split(text)
        name = tokens[0].lower()
        args = []
        flags: dict[str, str | bool] = {}

        for token in tokens[1:]:
            if token.startswith("/"):
                flags[token.lower()] = True
            elif token.startswith("-") and len(token) > 1:
                flags[token.lower()] = True
            else:
                args.append(token)

        return ParsedCommand(raw=raw, name=name, args=args, flags=flags)
