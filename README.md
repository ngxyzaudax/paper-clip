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
| `src/serialization/encode/` | Encoder, QR header, calibration strip, tag grid |
| `src/serialization/decode/` | QR, AprilTag mesh dewarp, cell classification, RS, decrypt |
| `src/ml/` | TensorFlow 2 cell decoder, synthetic trainer, saved-model loading |
| `src/scan_sim/` | Shared print/scan augmentation used by tests and training |
| `models/cell_decoder.keras` | Synthetic cell decoder shipped with the repo |
| `scripts/sweep_decode.py` | Heavier decode success-rate sweep |
| `tests/` | Fast pytest subset (`pytest`, skips `slow`) |

Runtime data lives under **`data/`**, mainly `jobs/` (`digital/`, `scans/`, etc.).

---

## Format

One layout. The printed page carries every parameter the decoder needs. Defaults target an Epson ET-8500 used with Epson’s own driver at about **720 dpi**: **A4**, **12 mm** margins, **32 px** cells (about 1.13 mm), a **5-symbol** alphabet, **16 mm** tag pitch, and **45%** Reed–Solomon redundancy. Cell size, alphabet (5, 8, or 11), and dpi are configurable. Cells must be at least **0.6 mm**.

### Header

The QR payload is the base64 of a **78-byte** big-endian record (74-byte body plus CRC-32). QR code **version 10**, error correction **H**, **4** quiet-zone modules, module size **0.36 mm**, drawn at its native module size.

| Field | Width | Meaning |
| --- | --- | --- |
| magic | 4 | `PCLP` |
| tag_pitch_mm | 1 | AprilTag pitch in whole millimetres (default 16) |
| flags | 1 | `0x01` when the payload uses a user passphrase |
| num_symbols | 1 | Alphabet size, including blank (5, 8, or 11) |
| cell_size_px | 2 | Cell edge in pixels at `print_dpi` |
| ecc_sym | 1 | Reed–Solomon parity symbols per block |
| print_dpi | 2 | Layout dpi |
| margins | 8 | Top, right, bottom, left, each `uint16` hundredths of a millimetre |
| page size | 4 | Width and height, each `uint16` hundredths of a millimetre |
| grid | 4 | Column count and row count |
| pages | 6 | Page index, total pages, data pages |
| payload_length | 4 | Interleaved stream length in bytes |
| original_length | 4 | Original file length in bytes |
| original_sha256 | 32 | SHA-256 of the original file |
| crc32 | 4 | CRC-32 of the preceding 74 bytes |

`ecc_sym` is `ceil(200 × redundancy)`. The default redundancy **0.45** stores **90** parity symbols. Each block is **165** data bytes and a **255**-byte codeword (`min(200, 255 − ecc_sym)` data bytes). The byte codec corrects 45 errors, or up to 90 erasures, per block. The decoder uses `ecc_sym` from the header.

### Page

Usable area is the page inside the margins, snapped to the cell grid. The header band holds the QR code at the top-left and a calibration strip of two rows by `num_symbols` colour cells. The strip sits to the right of the QR code when it fits, and under it otherwise. The band height is rounded up to a whole number of cells.

AprilTag **36h11** marks cover the data area. Each tag is **8 mm** with a **1.8 mm** quiet zone. The pitch byte sets how many tags fit: at least the tag plus both quiet zones, and at least `tag_pitch_mm`. The grid is 2–5 columns and 2–6 rows. Tag id is `row × columns + column`. Tags are drawn last, and each quiet zone is snapped onto the cell grid so it does not cut a neighbouring dot. Dots use **0.62** of the cell and do not touch.

At the A6 test settings (360 dpi, 18 px cells, 10 mm margins, 5 symbols) the page is 1488×2098 px, the mesh is **6×5** tags, and the data capacity is **774 bytes**. The default A4 page (720 dpi, 32 px cells, 12 mm margins, 5 symbols) holds **9450 bytes**, also on a 6×5 mesh.

### Payload and parity

The file is compressed with Zstandard and encrypted with Argon2id + AES-GCM. A built-in key is used when no passphrase is given. Inside the Reed–Solomon stream, three copies of a 7-byte header (`uint32` blob length, `uint16` block count, `uint8` filename length) precede the filename and the ciphertext. Copies are majority-voted on decode.

Optional parity pages are a second Reed–Solomon code along the page axis: one symbol per byte position, short pages zero-padded, `total_pages − data_pages` parity symbols. If decryption, the SHA-256, or the byte code fails and a parity page is present, the decoder drops the data page with the most erasures and rebuilds that page.

### Decode and tests

`paper-clip decode` loads a scan, reads the QR header, finds the tag grid, and dewarps with a piecewise mesh whose border homography is pinned to the corner tags. Cells are sampled on that grid. Colour classification uses a mild unsharp mask (amount 0.75, sigma 0.7 px) and a median of radius `dot_radius / 4`. A saved TensorFlow 2 network is used when `models/cell_decoder.keras` is present; otherwise, or with `--no-model`, classification is nearest-colour in Lab against the calibration strip. Low confidence becomes Reed–Solomon erasures. Then decrypt, decompress, reassemble, and check the original SHA-256.

`uv run pytest` runs the fast suite. `uv run python scripts/sweep_decode.py` reports success, pre-RS symbol error, erasures, and decode time across strengths, payload sizes, and both decoders (20 fixed-seed samples by default). `uv run python scripts/train_cell_decoder.py` retrains the cell decoder on the same photometric and ink model.

---

## Python dependencies

Core dependencies are declared in `pyproject.toml` and pinned in `uv.lock`.

Hardware discovery integrations are optional and installed with:

```bash
uv sync --extra hardware
```

This extra includes `pycups` and `python-sane`.
