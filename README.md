# paper-clip

Serialize files to **physical paper** as high-resolution PNGs: a color-coded dot grid carries compressed, error-corrected data with QR headers and calibration marks. Scan or photograph the pages to recover the original file. Optional encryption, page-level parity, and SANE/CUPS integration support real print-and-scan workflows.

- **Python:** 3.13+ (see `.python-version`)
- **CLI:** [Typer](https://typer.tiangolo.com/) — run `paper-clip` with arguments, or launch with **no arguments** for the [Textual](https://textual.textualize.io/) TUI.

---

## Prerequisites

- **[uv](https://docs.astral.sh/uv/)** — required. Install it [using the official instructions](https://docs.astral.sh/uv/getting-started/installation/) for your OS.
- **Scanner / printer (optional):** [SANE](https://sane-project.gitlab.io/) for `scan` and `capture`, [CUPS](https://www.cups.org/) for `print` and `capture`. The Python packages `python-sane` and `pycups` need those backends available on the machine.

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
| `encode` | File → PNG page(s) |
| `decode` | Image or folder of images → restored file |
| `scan` | SANE → PNGs (jobs or session folder) |
| `capture` | Encode, print, scan loop |
| `print` | Send images to CUPS |
| `devices` | Scanner / printer discovery and setup helpers |
| `info` | Capacity and layout for a config profile |
| `verify` | Encode in memory → decode → compare to source |
| `config` | Manage TOML profiles under `data/configs/` |
| `generate` | Random payload sized to N pages → encode into a job |
| `extract-training`, `train` | Training data and TensorFlow cell classifier (`[ml]`; `ml.*` modules) |

Use `uv run paper-clip <command> --help` for flags (passphrase, classifier `auto`/`ml`/`rgb`, DPI, jobs, etc.), or run `paper-clip` directly after activating `.venv`.

---

## Project layout

| Path | Role |
|------|------|
| `src/main.py` | Logging and Typer entry |
| `src/cli/` | Commands, Rich output, `cli/tui/` screens |
| `src/common/` | Config, codec, compression, crypto, CUPS/SANE, layouts, types |
| `src/serialization/encode/` | Encoder, pipeline, rendering, parity pages |
| `src/serialization/decode/` | Load pages, align, read grid, decode |

Runtime data lives under **`data/`**: `configs/` (profiles), `jobs/` (`digital/`, `scans/`, `decoded/`), and optionally `training/` and `models/` for ML.

---

## How the format works

1. **Payload:** SHA-256 hash, **Zstandard** compression, optional **Argon2id + AES-GCM** encryption, **Reed–Solomon** on blocks with **interleaving**, plus a small repeated payload header (lengths, filename).

2. **Symbols:** Bytes map to a multi-level alphabet (`num_colors`); more than one bit per cell when `num_colors` > 2 (`common/symbols.py`).

3. **Pages:** PNG at `scan_dpi` with finders/alignment, **QR** header, optional **palette QR**, calibration bar, timing tracks, and the data grid (`serialization/encode/renderer.py`).

4. **Parity:** Extra pages from RS across pages can recover missing data pages when `redundancy_pages` > 0 (`common/fountain.py`).

5. **Decode:** Deskew, align, sample cells, classify (RGB distance to references or optional ML), then reverse RS, decompress, decrypt, and verify the hash (`serialization/decode/`).

---

## Python dependencies (core)

Typer, Rich, Textual, Pillow, NumPy, OpenCV (headless), scikit-image, AprilTag bindings, zstandard, reedsolomon, cryptography, Argon2, QR/barcode libraries, `python-sane`, `pycups`, and related stack — see `pyproject.toml` and `uv.lock` for exact versions.
