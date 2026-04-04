# paper-clip

Serialize files to **physical paper** as high-resolution PNGs: a color-coded dot grid carries compressed, error-corrected data with QR headers and calibration marks. Optional encryption and page-level parity are supported. The CLI and TUI focus on **encoding** and **hardware discovery** (printers and scanners).

- **Python:** 3.13+ (see `.python-version`)
- **CLI:** [Typer](https://typer.tiangolo.com/) — run `paper-clip` with arguments, or launch with **no arguments** for the [Textual](https://textual.textualize.io/) TUI.

---

## Prerequisites

- **[uv](https://docs.astral.sh/uv/)** — required. Install it [using the official instructions](https://docs.astral.sh/uv/getting-started/installation/) for your OS.
- **Scanner / printer (optional):** for the `devices` command and **Devices** TUI tab, [SANE](https://sane-project.gitlab.io/) and [CUPS](https://www.cups.org/) backends plus the `python-sane` and `pycups` packages let the app list hardware and save defaults.

---

## Setup

From the repository root:

1. **Install dependencies and the project** (uses `uv.lock` for a reproducible environment):

   ```bash
   uv sync
   ```

   This creates `.venv/`, selects Python **3.13** (installing it via uv if needed, guided by `.python-version`), and installs **paper-clip** in editable mode.

2. **Check that the CLI is available:**

   ```bash
   uv run paper-clip --help
   ```

3. **(Optional) ML training and TensorFlow-backed decode path** — install the extra dependency group from `pyproject.toml`:

   ```bash
   uv sync --extra ml
   ```

### Everyday commands

| Task | Command |
|------|---------|
| Run CLI without activating the venv | `uv run paper-clip <subcommand> [options]` |
| Activate the venv manually | `source .venv/bin/activate` (Unix) — then `paper-clip` |
| Refresh the lockfile after changing `pyproject.toml` | `uv lock` |
| Reinstall from the updated lockfile | `uv sync` |

---

## CLI overview

| Command | Purpose |
|---------|---------|
| `encode` | File → PNG page(s) (same workflow as **Encode File** in the TUI) |
| `devices` | Scanner / printer discovery and defaults (same as **Devices** in the TUI) |

Use `uv run paper-clip <command> --help` for flags, or run `paper-clip` with no arguments for the TUI.

---

## Project layout

| Path | Role |
|------|------|
| `src/main.py` | Logging and Typer entry |
| `src/cli/` | Commands, Rich output, `cli/tui/` screens |
| `src/common/` | Config, codec, compression, crypto, CUPS/SANE, layouts, types |
| `src/serialization/encode/` | Encoder, pipeline, rendering, parity pages |

Runtime data lives under **`data/`**, mainly `jobs/` (`digital/`, `scans/`, etc.).

---

## How the format works

1. **Payload:** SHA-256 hash, **Zstandard** compression, optional **Argon2id + AES-GCM** encryption, **Reed–Solomon** on blocks with **interleaving**, plus a small repeated payload header (lengths, filename).

2. **Symbols:** Bytes map to a multi-level alphabet (`num_colors`); more than one bit per cell when `num_colors` > 2 (`common/symbols.py`).

3. **Pages:** PNG at `print_dpi` with finders/alignment, **QR** header, optional **palette QR**, calibration bar, timing tracks, and the data grid (`serialization/encode/renderer.py`).

4. **Parity:** Extra pages from RS across pages can recover missing data pages when `redundancy_pages` > 0 (`common/fountain.py`).

---

## Python dependencies (core)

Typer, Rich, Textual, Pillow, NumPy, OpenCV (headless), scikit-image, AprilTag bindings, zstandard, reedsolomon, cryptography, Argon2, QR/barcode libraries, `python-sane`, `pycups`, and related stack — see `pyproject.toml` and `uv.lock` for exact versions.
