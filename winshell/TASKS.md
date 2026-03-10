# WinShell Task Backlog (Codex-ready)

Use this as a parallelizable task board for coding agents.

## Priority labels
- **P0** = must-have for reliable usage
- **P1** = strong usability/ops value
- **P2** = nice-to-have / enhancement

---

## P0 — Stability and correctness

### T-001 Command coverage audit
- Verify every documented command exists and returns clear output/errors.
- Ensure unsupported forms return consistent Windows-like messaging.
- **Done when:** README and runtime behavior match 1:1.

### T-002 Add automated tests (parser/registry/formatter)
- Add `pytest`.
- Parser tests for flags/args.
- Registry tests for routing and usage errors.
- Formatter golden tests for `ipconfig`, `ipconfig /all`, `systeminfo`.
- **Done when:** CI-friendly test suite passes locally.

### T-003 Subprocess hardening
- Centralize timeout and error handling.
- Standardize command-not-found behavior.
- Ensure all subprocess calls use list args (no unsafe shell usage).
- **Done when:** adapters share a robust command runner contract.

---

## P1 — Network operations features

### T-101 Add `route print`
- Implement Windows-like route table view.
- Backend from `netstat -rn` and default route parsing.

### T-102 Add `getmac`
- Show interface -> MAC mapping in Windows-like style.

### T-103 Add connectivity test command
- `test-netconnection <host> -port <n>` (or equivalent WinShell syntax).
- Include DNS resolution, TCP connect result, latency summary.

### T-104 Improve `tracert` formatter
- Parse hops cleanly.
- Normalize timeout/unreachable lines to readable Windows-like output.

### T-105 Add `ipconfig /flushdns` (guarded)
- Add clear warning/permission prompt text.
- Document that admin rights may be required.

---

## P1 — Product usability

### T-111 Help UX overhaul
- Group commands by category (network/system/shell).
- Add short examples and common troubleshooting flows.

### T-112 Output themes
- Optional classic CMD color style.
- Keep default accessible and readable.

### T-113 Export/report command
- `export <file>` to write command transcript/report.
- Include timestamp + host metadata.

---

## P1 — Packaging and distribution

### T-121 Add `.app` packaging pipeline
- Add PyInstaller config/spec.
- Bundle icon `assets/WinShell.icns`.

### T-122 Add `.dmg` packaging script
- Scriptable local build for DMG output.
- Include Applications alias in image.

### T-123 GitHub Actions release workflow
- Trigger on tags.
- Build app + dmg.
- Upload artifacts to release.

### T-124 Signing + notarization documentation
- Step-by-step maintainer guide with required secrets/certs.

---

## P2 — Advanced monitoring mode

### T-201 Live monitor mode
- Periodic checks: packet loss, latency, DNS resolution, gateway reachability.
- Alert on threshold breach.

### T-202 Snapshot + compare
- Save network state snapshots.
- Compare current vs previous and show deltas.

### T-203 Interface diagnostics panel
- Wi-Fi RSSI/noise/channel where available.
- Wired/wireless status summary.

---

## Suggested parallel split for two Codex agents

### Agent A (platform + quality)
- T-002, T-003, T-121, T-123

### Agent B (features + UX)
- T-101, T-102, T-104, T-111

Then merge and run joint smoke test.
