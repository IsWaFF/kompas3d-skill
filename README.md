# KOMPAS-3D: Claude Code skill

[![lint](https://github.com/IsWaFF/kompas3d-linux-skill/actions/workflows/lint.yml/badge.svg)](https://github.com/IsWaFF/kompas3d-linux-skill/actions/workflows/lint.yml)

**[Русская версия](README.ru.md)**

A [Claude Code](https://claude.com/claude-code) skill and Python helpers that drive **KOMPAS-3D v25** through its Python API (`ksapi`). With them, Claude can build 2D fragments and drawings: geometry, dimensions, fills, PNG export. The repo also has a Linux launcher that stops KOMPAS from taking down a Wayland session.

| Platform | Status |
|---|---|
| Linux, KOMPAS in a distrobox | Tested with KOMPAS-3D v25 Home |
| Linux, native install | Should work (`KOMPAS_BOX=none`), not tried with KOMPAS |
| Windows | Should work: ASCON documents the same Python API there. The script runner is tested on Windows with a stub API, but KOMPAS on Windows has not been tried yet. [Tell us](https://github.com/IsWaFF/kompas3d-linux-skill/issues) how `examples/selftest.py` goes. |

<p align="center">
  <img src="docs/flange.png" width="520" alt="Flange drawn by examples/flange.py">
  <br><sub>Drawn entirely through the API by <a href="examples/flange.py">examples/flange.py</a>: trimmed geometry, dimensions, overlap check.</sub>
</p>

## What's inside

| Path | What it is |
|---|---|
| [`skill/kompas-3d/SKILL.md`](skill/kompas-3d/SKILL.md) | The skill: setup, workflow for a drawing task, and a list of API gotchas checked on v25 |
| [`skill/kompas-3d/scripts/ks.py`](skill/kompas-3d/scripts/ks.py) | Helpers: `seg` `arc` `circle` `polygon` `text`, `rdim` `ddim` `ldim` `adim`, `fill`, `overlaps`, `export_png`, `save` |
| [`skill/kompas-3d/scripts/run.py`](skill/kompas-3d/scripts/run.py) | Runs a Python script against the running KOMPAS: inside the distrobox on Linux, directly on Windows (`run.sh` is a Linux shortcut) |
| [`skill/kompas-3d/scripts/pdf_images.py`](skill/kompas-3d/scripts/pdf_images.py) | Pulls figures and text out of an assignment PDF |
| [`launcher/kompas-nested`](launcher/kompas-nested) | Linux: starts KOMPAS inside Xephyr + openbox |
| [`examples/`](examples) | `flange.py` (the picture above) and `selftest.py` (checks every helper against your KOMPAS) |
| [`tests/`](tests) | CI check of `run.py` on Linux and Windows against a stub API |

## Why

- **The API is barely documented, and some calls don't do what their names say.** Examples:
  - `SetDirection` on arcs sometimes draws the other part of the circle;
  - angle dimensions built from points measure the second ray from the sheet origin;
  - diametral dimensions ignore `SetShelfAngle`/`SetShelfLength`;
  - raster export is greyscale by default and hangs on a modal dialog if the file exists.

  The skill records what actually works, so Claude doesn't relearn it every session.
- **On Linux, KOMPAS kills swayfx.** Its context panel is an XWayland popup that maps and unmaps very fast, and swayfx 0.6 aborts on it, taking the whole session down. `kompas-nested` runs KOMPAS inside a nested X server, so the compositor only sees one ordinary window.

## Requirements

- KOMPAS-3D v25. Home is enough.
- [Claude Code](https://claude.com/claude-code) for the skill part. The helpers work on their own too.
- **Linux:**
  - [distrobox](https://distrobox.it/) (podman or docker) with an Ubuntu 24.04 box, and KOMPAS installed inside it from ASCON's apt repository following their instructions. Tested: v25 Home 25.0.1.2738 (`ascon-kompas3d-home-v25-full`).
  - In the box, for the launcher: `xserver-xephyr openbox x11-xkb-utils`.
- **Windows:** 64-bit Python 3 (`ksapi.py` loads a 64-bit DLL).

## Install

Linux:

```bash
# once: the box (then install KOMPAS inside it as ASCON describes)
distrobox create -n kompas-box -i ubuntu:24.04
distrobox enter kompas-box -- sudo apt install -y xserver-xephyr openbox x11-xkb-utils

git clone https://github.com/IsWaFF/kompas3d-linux-skill
cd kompas3d-linux-skill
./install.sh            # or ./install.sh --link to symlink instead of copying
```

`install.sh` puts the skill in `~/.claude/skills/kompas-3d`, the launcher in `~/.local/bin/kompas-nested` and a «KOMPAS-3D (nested)» menu entry. Anything already there is moved to `~/.claude/backups/kompas-3d-install-<timestamp>/`. `CLAUDE_CONFIG_DIR`, `BIN_DIR` and `XDG_DATA_HOME` change the targets.

Windows (PowerShell):

```powershell
git clone https://github.com/IsWaFF/kompas3d-linux-skill
cd kompas3d-linux-skill
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills" | Out-Null
Copy-Item -Recurse skill\kompas-3d "$env:USERPROFILE\.claude\skills\"
```

## Use

Start KOMPAS (on Linux with `kompas-nested`), then ask Claude Code, for example «начерти в компасе фланец Ø120 с четырьмя отверстиями». The skill triggers on КОМПАС / чертёж / фрагмент.

Without Claude:

```bash
python3 skill/kompas-3d/scripts/run.py examples/selftest.py   # smoke test of every helper (Windows: py instead of python3)
python3 skill/kompas-3d/scripts/run.py examples/flange.py ~/out   # -> ~/out/flange.frw, ~/out/flange.png
```

```python
import ks

ks.new_fragment()                 # experiments go into a new document, not the user's
ks.circle(0, 0, 30)               # contour + centre lines
ks.ddim(0, 0, 30, 45)             # Ø60
assert ks.overlaps() == []        # no stacked lines
ks.save('/home/me/part.frw')
ks.export_png('/home/me/part.png')
```

## Configuration

| Variable | Default | Used by |
|---|---|---|
| `KOMPAS_DIR` | `/opt/ascon/kompas3d-v25`, Windows: `C:\Program Files\ASCON\KOMPAS-3D v25` | `run.py`, launcher |
| `KOMPAS_BOX` | `kompas-box`; `none` = KOMPAS installed natively | `run.py` (Linux), launcher |
| `T` | `120` | `run.py` timeout, seconds |
| `KOMPAS_BIN` | `kHome` | launcher |
| `KOMPAS_DISPLAY` | `:5` | launcher |
| `KOMPAS_SCREEN` | `1400x850` | launcher (initial size, the window resizes) |
| `KOMPAS_XKB_LAYOUT` / `KOMPAS_XKB_OPTION` | `us,ru` / `grp:alt_shift_toggle` | launcher |
| `KOMPAS_OB_RC` | `~/.config/kompas-nested/rc.xml` | launcher (generated from the stock openbox config on first run) |

On sway, [`launcher/sway.conf`](launcher/sway.conf) keeps the Xephyr window tiled. It also has rules for running KOMPAS directly on XWayland, which make crashes rarer but don't stop them.

## Limitations

- Tested with KOMPAS on one setup: Garuda Linux, swayfx 0.6, KOMPAS-3D v25 Home. Other compositors, editions and Windows should work but haven't been tried with KOMPAS.
- 2D only (fragments and drawings).
- Linux: the API needs a real display. Under Xvfb the licence window never finishes and the API port never opens. Run it in a desktop session.

## Development

- When Claude learns something new about the API, it updates `SKILL.md` or `ks.py` (see «Improving this skill» at the end of `SKILL.md`).
- After code changes, run:
  - `examples/selftest.py` against a real KOMPAS;
  - `ruff check .`;
  - `shellcheck` on the shell scripts.
- CI runs the linters plus `tests/probe.py` through `run.py` on Ubuntu and Windows.

## License

[MIT](LICENSE). KOMPAS-3D is a trademark of ASCON. This project is not affiliated with ASCON. `ksapi.py` and the KOMPAS SDK are not included: they come with your KOMPAS installation.

Built together with Claude Code.
