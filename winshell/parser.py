import shlex

from winshell.models import ParsedCommand


class CommandParser:
    def parse(self, raw: str) -> ParsedCommand:
        text = (raw or "").strip()
        if not text:
            return ParsedCommand(raw=raw, name="", args=[], flags={}, tokens=[])

        tokens = shlex.split(text)
        name = tokens[0].lower()
        args = []
        flags: dict[str, str | bool] = {}
        index = 1

        while index < len(tokens):
            token = tokens[index]
            if token.startswith("/"):
                key = token.lower()
                next_token = tokens[index + 1] if index + 1 < len(tokens) else None
                if next_token and not next_token.startswith(("/", "-")):
                    flags[key] = next_token
                    index += 2
                    continue
                flags[key] = True
            elif token.startswith("-") and len(token) > 1:
                key = token.lower()
                next_token = tokens[index + 1] if index + 1 < len(tokens) else None
                if next_token and not next_token.startswith(("/", "-")):
                    flags[key] = next_token
                    index += 2
                    continue
                flags[key] = True
            else:
                args.append(token)
            index += 1

        return ParsedCommand(raw=raw, name=name, args=args, flags=flags, tokens=tokens)
