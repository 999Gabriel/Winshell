# Contributing to WinShell

Thanks for helping improve WinShell.

WinShell is designed for students and network employees who need a Windows-like command experience on macOS. Contributions should keep that audience in mind: **clarity, reliability, and familiar UX first**.

## Development setup

```bash
cd winshell
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m winshell
```

## Project architecture

- `winshell/tui/` – Textual app and user interaction
- `winshell/parser.py` – command parsing
- `winshell/registry.py` – command routing and execution
- `winshell/adapters/` – macOS command adapters
- `winshell/formatters/` – Windows-style output formatting

## Contribution principles

1. **Windows-like UX:** command names, error style, and formatting should feel familiar.
2. **Safe subprocess usage:** no shell injection patterns; prefer explicit argument lists.
3. **Readable output:** avoid dumping raw noisy macOS output when a formatter can improve it.
4. **Modular changes:** parser/adapter/formatter/registry should stay cleanly separated.
5. **Backward compatibility:** do not break existing supported commands.

## Adding a new command (recommended flow)

1. Add parser support only if needed.
2. Implement backend logic in `adapters/`.
3. Add output shaping in `formatters/`.
4. Register command behavior in `registry.py`.
5. Add or update tests.
6. Document command in `README.md`.

## Testing expectations

Before opening a PR, validate:

- Core commands run: `help`, `ipconfig`, `ipconfig /all`, `systeminfo`, `exit`
- Unknown command handling is still Windows-like
- UI history and clear behavior still works (`↑`, `↓`, `cls`, `Ctrl+L`)

If tests exist, run them and include output in the PR.

## Pull request checklist

- [ ] Code follows architecture boundaries
- [ ] No unsafe subprocess/shell patterns
- [ ] New/changed commands documented
- [ ] Tests added/updated
- [ ] Manual smoke test completed

## Release-minded changes

If your PR affects packaging or app behavior, update:

- `docs/release.md`
- any build scripts/specs used for `.app`/`.dmg`

Thanks for contributing.
