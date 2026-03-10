# WinShell Release Checklist (.app + .dmg)

This checklist is for maintainers preparing a release for students and network employees.

## 1) Pre-release quality gate

- [ ] Update version number
- [ ] Confirm README command list matches implementation
- [ ] Confirm icon assets exist:
  - `assets/WinShell.icns`
  - `assets/winshell_app_icon.jpg`
- [ ] Run smoke tests for key commands
- [ ] Review known issues and decide release scope

## 2) Build validation (source)

```bash
cd winshell
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m winshell
```

Manual checks:
- [ ] App launches
- [ ] `help` output is correct
- [ ] `ipconfig` and `ipconfig /all` look clean
- [ ] `tracert <host>` formatting is readable
- [ ] `systeminfo` summary renders

## 3) Package .app

Suggested tooling: `pyinstaller`

Example (adjust once spec is finalized):

```bash
pyinstaller --noconfirm --windowed --name WinShell --icon assets/WinShell.icns winshell/__main__.py
```

- [ ] Verify app opens on clean macOS user account
- [ ] Verify no missing runtime dependencies

## 4) Package .dmg

Suggested tooling: `create-dmg` or `dmgbuild`

- [ ] DMG contains `WinShell.app`
- [ ] Includes Applications shortcut for drag/drop install
- [ ] Volume name and branding are correct

## 5) Sign + notarize (recommended for org rollout)

- [ ] Sign app bundle with Developer ID
- [ ] Notarize build with Apple
- [ ] Staple notarization ticket
- [ ] Verify Gatekeeper acceptance on another machine

## 6) GitHub Release

- [ ] Tag release (`vX.Y.Z`)
- [ ] Add release notes (features, fixes, known issues)
- [ ] Upload `.dmg`
- [ ] Include checksums
- [ ] Link installation steps in notes

## 7) Post-release

- [ ] Gather feedback from student and employee users
- [ ] Track command requests and formatting pain points
- [ ] Schedule patch release for urgent issues
