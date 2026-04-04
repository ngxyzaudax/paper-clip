# paper-clip

Serialize files to **physical paper** as high-resolution images: a dense grid of colored cells carries the payload, with machine-readable headers, calibration aids, and optional redundancy and encryption. Scan the pages (or load camera images) to recover the original bytes.

**Python:** 3.13+  
**Entry point:** `paper-clip` (Typer CLI). With no arguments, it starts a **Textual** TUI that wraps the same workflows.

---

## What the format does

1. **Payload preparation** (`common/`, `serialization/encode/encoder.py`): Input bytes are hashed (SHA-256), **compressed** with Zstandard, optionally **encrypted** (Argon2id key derivation + AES-GCM), then protected with **Reed–Solomon** on fixed-size blocks. Codewords are **interleaved** across blocks to spread burst errors. A small redundant payload header repeats metadata (compressed length, block count, original filename).

2. **Symbol mapping** (`common/symbols.py`): Payload bytes map to **multi-level symbols** (one of `num_colors` discrete colors per cell), so each cell carries more than one bit when `num_colors` > 2.

3. **Page rendering** (`serialization/encode/renderer.py`, `grid_renderer.py`): Each page is a PNG at `scan_dpi` with:
   - **Finder / alignment** patterns (including AprilTag-related layout in `serialization/encode/alignment.py` and `common/apriltag_markers.py`)
   - A **QR code** header with binary metadata (`serialization/encode/qr_header.py`)
   - Optional **palette QR** when colors are calibrated (`FLAG_HAS_PALETTE_QR`)
   - **Calibration** bar, **timing** tracks, and a **data grid** of colored cells
   - Optional **info panel** with human-readable page stats

4. **Parity pages** (`common/fountain.py`, `serialization/encode/parity_render.py`): If `redundancy_pages` > 0, extra pages are generated so missing or damaged **data** pages can be reconstructed using RS erasure coding across pages.

5. **Decoding** (`serialization/decode/`): Images are loaded and sorted, **deskewed**, calibration references extracted, the grid **aligned** and **sampled**, then each cell is classified to a symbol—either **vector/RGB** distance to references or an optional **ML classifier**. Payload is reassembled, RS and compression (and decryption) reversed, and the file verified against the embedded hash.

---

## CLI commands

| Command | Role |
|--------|------|
| `encode` | File → PNG page(s) under a chosen profile/config |
| `decode` | Image or directory of images → restored file |
| `scan` | SANE scanner → PNGs (job layout or session folder); can average into a master |
| `capture` | Encode, print, scan loop for end-to-end physical round-trips |
| `print` | Send images to CUPS with optional capability checks |
| `devices` | Discover / configure scanners and printers (TUI helpers) |
| `info` | Show capacity, grid, and layout stats for a profile |
| `verify` | Encode in memory → decode → compare to source (sanity check) |
| `config` | List/show/save **TOML** profiles (`data/configs/*.toml`) |
| `generate` | Random test payload sized to N pages, encode into a job |
| `extract-training` / `train` | Build TFRecord pairs from jobs and train a TensorFlow cell classifier (optional `[ml]` install; imports live under `ml.*` alongside `src/`) |

Run `paper-clip --help` and `paper-clip <command> --help` for options (passphrases, classifier mode `auto`/`ml`/`rgb`, job IDs, DPI, etc.).

---

## Project layout

- `src/main.py` — logging setup and Typer app entry
- `src/cli/` — commands, Rich output, Textual screens (`cli/tui/`)
- `src/common/` — config, codec, compression, crypto, CUPS/SANE helpers, data paths, palettes, page layout, types
- `src/serialization/encode/` — encoder, pipeline, rendering (grid, QR, calibration, parity)
- `src/serialization/decode/` — page load, align, grid read, decoder, QR/palette readers

**Local data** (created at runtime): under `data/` — `configs/` (profiles), `jobs/` (digital/scans/decoded per job), `training/` and `models/` when using ML workflows.

---

## Install

From the repository root (prefer a virtual environment):

```bash
pip install -e .
```

Optional TensorFlow-based training and ML decode path:

```bash
pip install -e ".[ml]"
```

Core dependencies include Typer, Rich, Textual, Pillow, NumPy, OpenCV (headless), scikit-image, AprilTag bindings, zstandard, reedsolomon, cryptography, Argon2, QR and barcode libraries, **python-sane**, and **pycups**. Scanner and printer support depends on a working SANE and CUPS setup on the host.
