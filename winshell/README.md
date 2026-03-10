# WinShell (macOS)

WinShell is a terminal TUI app that gives a Windows-like command experience on macOS for NWES school network administration lessons.

It translates familiar commands (`ipconfig`, `tracert`, etc.) into macOS-compatible commands and formats output in a cleaner Windows-style view.

## Features

- Textual-based terminal UI (header, output pane, input prompt, footer/help)
- Windows-style command parser
- Modular architecture:
  - `winshell/tui` – UI app
  - `winshell/parser.py` – parsing of command + flags
  - `winshell/registry.py` – command routing/execution
  - `winshell/adapters` – macOS command adapters
  - `winshell/formatters` – Windows-like output formatting
- Command history via Up/Down keys
- Unknown command handling with CMD-like error text
- `cls` to clear output

## Supported Commands

- `ipconfig`
- `ipconfig /all`
- `ping <host>`
- `tracert <host>`
- `netstat`
- `arp -a`
- `nslookup <host>`
- `hostname`
- `whoami`
- `systeminfo`
- `cls`
- `help`
- `exit`

## Installation

```bash
cd winshell
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python -m winshell
```

## Example Commands

```text
ipconfig
ipconfig /all
ping 8.8.8.8
tracert cloudflare.com
netstat
arp -a
nslookup apple.com
systeminfo
help
```

## Notes

- This is **Windows-like**, not a full PowerShell clone.
- Output is intentionally simplified for teaching readability.
- `tracert` uses `traceroute` underneath.
- `systeminfo` combines `sw_vers`, `uname`, `sysctl`, and `system_profiler`.
