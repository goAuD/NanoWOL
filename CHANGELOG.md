# Changelog

All notable changes to NanoWOL will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.2.2] - 2026-01-27

### Added
- Replay protection for shutdown commands (timestamp + nonce).
- Centralized version management via `version.py`.

### Changed
- Package renamed from `wherewol` to `nanowol` in pyproject.toml.
- Python version requirement updated to 3.9+ (aligned with pyproject.toml).
- CLI and WebUI now use replay-protected payloads for shutdown.
- Web UI footer now uses template variable for version display.

### Security
- Shutdown commands now include timestamp and nonce to prevent replay attacks.
- Agent rejects expired (>60s) or reused nonces.
- Backward compatible with legacy signature format.

### Fixed
- pyproject.toml URLs now point to correct NanoWOL repository.
- Version mismatch between code (1.2.0) and UI footer (1.2.1).

---

## [1.2.1] - 2026-01-23

### Added
- `static/nano-webui.css` reusable CSS for Nano web interfaces.
- `static/NANO_WEBUI_GUIDE.md` comprehensive usage documentation.
- Unified styling with CSS custom properties.
- Components: cards, buttons, inputs, toasts, status indicators.

### Fixed
- Cross-platform fixes and sudo check.

### Changed
- README rewrite and WebUI styling unification.

---

## [1.2.0] - 2026-01-20

### Added
- Auto-start Service: agent can run as a system service.
  - Windows: Task Scheduler (boot trigger).
  - Linux: systemd user service.
  - macOS: launchd user agent.
- New CLI commands: `install-service`, `uninstall-service`, `service-status`.
- `service.py` module for cross-platform service management.
- 12 unit tests (3 new for service module).

### Changed
- Version bumped to 1.2.0.
- README updated with platform support table.

---

## [1.0.0] - 2026-01-13

### Added
- Unified single-file CLI (`wherewol.py`).
- RSA-2048 signed shutdown commands.
- Wake-on-LAN support.
- Modern cyberpunk web interface.
- Works with Tailscale/WireGuard VPN.

### Notes
- Initial public release under the name **WhereWol**.
