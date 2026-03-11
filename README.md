# WinShell

WinShell is a terminal-based TUI for macOS that presents common system and networking commands in a Windows-like style. It is intended for NWES and general school lab work where students already know `ipconfig`, `tracert`, or `systeminfo`, but are working on macOS.

The app does not try to clone PowerShell. It provides a simplified Windows-flavored interface, translates supported commands to macOS tooling, and formats the output so it is easier to read in class.

## Features

- Textual TUI with header, scrollable output history, command line, and footer shortcuts
- Windows-style command parser with aliases and friendly error messages
- macOS adapters for common networking and system inspection commands
- Public-IP geolocation with map-ready coordinates and links
- LAN neighbor discovery with IP, MAC, interface, and reverse-DNS context
- Local/target device inspection with architecture and adapter summaries
- CMD mode and PowerShell mode prompt switch
- Command history with arrow keys
- Tab completion for supported commands
- Transcript export to a text file
- Clipboard copy support from inside the app via `copy` or `F6`

## Supported commands

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
- `geoip <ip-or-host>`
- `neighbors`
- `deviceinfo [ip-or-host]`
- `copy [all|last]`
- `cls`
- `help`
- `exit`

WinShell-specific additions:

- `mode cmd`
- `mode powershell`
- `export winshell-output.txt`

## Installation

```bash
cd /Users/gabriel/.openclaw/workspace/winshell
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Or install as a package:

```bash
pip install -e .
```

## Run

```bash
python3 -m winshell
```

Or, after editable installation:

```bash
winshell
```

## Example commands

```text
ipconfig
ipconfig /all
ping example.com
tracert example.com
nslookup openai.com
geoip 8.8.8.8
neighbors
deviceinfo localhost
copy
copy last
arp -a
netstat
systeminfo
mode cmd
export lesson-output.txt
```

## Notes

- `ipconfig` and `ipconfig /all` are formatted from macOS networking tools such as `ifconfig`, `route`, `networksetup`, and `scutil`.
- `geoip` uses a public geolocation API at runtime for public IP addresses and prints coordinates plus Apple Maps / Google Maps / OpenStreetMap links.
- `neighbors` uses the local ARP cache, so it is most useful after the Mac has recently talked to devices on the LAN.
- `deviceinfo` shows local architecture and adapter data directly; remote device architecture is intentionally reported as unknown unless there is a reliable local source.
- `copy` copies either the visible transcript or the last command output into the macOS clipboard using `pbcopy`.
- If a command syntax is recognized but not implemented, WinShell shows:
  `Command not supported yet in WinShell.`
- If a command is unknown, WinShell shows a Windows-like error:
  `'<command>' is not recognized as an internal or supported WinShell command.`

## Mock UI

See [docs/mockup.md](docs/mockup.md) for a text mock of the interface.
