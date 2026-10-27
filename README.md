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

3. **(Optional) hardware discovery support** — install scanner/printer integration extras:

   ```bash
   uv sync --extra hardware
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
| `decode` | Scanned PNG/JPEG/TIFF, a directory, or a scan job → original file |
| `devices` | Scanner / printer discovery and defaults (same as **Devices** in the TUI) |

Use `uv run paper-clip <command> --help` for flags, or run `paper-clip` with no arguments for the TUI.

---

## Project layout

| Path | Role |
|------|------|
| `src/main.py` | Logging and Typer entry |
| `src/cli/` | Commands, Rich output, `cli/tui/` screens |
| `src/common/` | Config, codec, compression, crypto, CUPS/SANE, layouts, types |
| `src/serialization/encode/` | Format v2 encoder, QR header, calibration strip, tag grid |
| `src/serialization/decode/` | QR, AprilTag mesh dewarp, cell classification, RS, decrypt |
| `src/ml/` | TensorFlow 2 cell decoder, synthetic trainer, saved-model loading |
| `src/scan_sim/` | Shared print/scan augmentation used by tests and training |
| `models/cell_decoder.keras` | Synthetic cell decoder shipped with the repo |
| `scripts/sweep_decode.py` | Heavier decode success-rate sweep |
| `tests/` | Fast pytest subset (`pytest`, skips `slow`) |

Runtime data lives under **`data/`**, mainly `jobs/` (`digital/`, `scans/`, etc.).

---

## How the format works

Format version is **2**. Defaults target an Epson ET-8500 used with Epson’s own driver at about **720 dpi**: **12 mm** margins, **32 px** cells (about 1.13 mm), and a **5-symbol** alphabet. Cell size, alphabet (5, 8, or 11), and dpi are configurable. Cells must be at least **0.6 mm**.

1. **Payload:** Zstandard, then Argon2id + AES-GCM (a built-in key when no passphrase is given). Filename, blob length, and block count are repeated inside the Reed–Solomon stream. The QR header stores dpi, margins, page size, the interleaved payload length, and the SHA-256 and length of the **original file**.

2. **Page:** A version-10 QR code drawn on its module grid, a calibration strip of the symbol colours, an AprilTag 36h11 grid for a mesh dewarp, and gapped colour dots. Tags are pasted last so they keep a quiet zone.

3. **Decode:** `paper-clip decode` loads a scan, reads the QR header, finds the tag grid, dewarps with a piecewise mesh (global homography if only a few tags are visible), samples cells, and classifies them. A saved TensorFlow 2 network is used when `models/cell_decoder.keras` is present; otherwise, or with `--no-model`, classification is nearest-colour in Lab against the calibration strip. Low confidence becomes Reed–Solomon erasures. Then decrypt, decompress, reassemble, and check the original SHA-256. Extra parity pages can rebuild a missing page.

4. **Tests:** `uv run pytest` runs the fast suite. `uv run python scripts/sweep_decode.py` reports decode success across augmentation strengths. `uv run python scripts/train_cell_decoder.py` retrains the cell decoder on the same photometric and ink model.

---

## Python dependencies

Core dependencies are declared in `pyproject.toml` and pinned in `uv.lock`.

Hardware discovery integrations are optional and installed with:

```bash
uv sync --extra hardware
```

This extra includes `pycups` and `python-sane`.
