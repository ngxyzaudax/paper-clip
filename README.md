# paper-clip

Serialize files to **physical paper** as high-resolution PNGs: a color-coded dot grid carries compressed, error-corrected data with QR headers and calibration marks. Optional encryption and page-level parity are supported. The CLI and TUI focus on **encoding** and **hardware discovery** (printers and scanners).

- **Python:** 3.13+ (see `.python-version`), on macOS or Linux
- **CLI:** [Typer](https://typer.tiangolo.com/) — run `paper-clip` with arguments, or launch with **no arguments** for the [Textual](https://textual.textualize.io/) TUI.

---

## Prerequisites

- **[uv](https://docs.astral.sh/uv/)** — required. Install it [using the official instructions](https://docs.astral.sh/uv/getting-started/installation/) for your OS.
- **Printer / scanner:** discovery, printing, and scanning use **IPP Everywhere** and **eSCL** (AirScan) on both macOS and Linux. No vendor driver, CUPS queue, or SANE backend is required. `pycups` is an optional extra on both. `python-sane` is an optional extra on Linux only; macOS has no SANE library.

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
| `decode` | Scanned PNG/JPEG/TIFF, a directory, or a scan job → original file. An existing file is kept, and the new one is saved as `name (1).ext`, unless `--force` is given |
| `print` | PNG page(s) → IPP Everywhere job (bordered, 100% scale, color; one-sided unless `--duplex`) |
| `scan` | One eSCL platen scan → JPEG or PNG |
| `devices` | IPP / eSCL discovery and the safe print ticket (same devices as the TUI) |
| `calibrate` | One duplex sheet that measures QR, AprilTag, dot, and symbol limits separately |

Use `uv run paper-clip <command> --help` for flags, or run `paper-clip` with no arguments for the TUI. The TUI sidebar follows the workflow: **1 Encode**, **2 Print**, **3 Scan**, **4 Decode**, then **5 Devices** and **6 Calibrate**. The number keys switch panels. After an encode, **Print this job** opens Print with that job selected. After a scan job, **Decode this job** opens Decode with it selected. Decode saves to `data/decoded/<job>/` without overwriting. Printing a job or the calibration sheet always asks first, and the button stays locked while a job is sending.

### Driverless printing and scanning

`paper-clip devices` browses mDNS for `_ipp._tcp`, `_ipps._tcp`, and `_uscan._tcp`. Queries go out from each IPv4 interface on its own ephemeral port, which is where the unicast reply comes back. A second socket listens on UDP port 5353 for multicast replies. macOS shares that port with mDNSResponder. Linux shares it with Avahi without `SO_REUSEPORT`, because that option would hand each multicast packet to only one listener. Saved device URIs use the literal address from the reply, so Linux does not need `nss-mdns` to resolve `.local`. A saved `printer.uri` or `scanner.uri` in `data/devices.json` is used as well. `printer.profile` stores the density calibration (`cell_size_px`, `num_symbols`, `tag_size_mm`, `tag_pitch_mm`, `print_dpi`, `qr_module_mm`, `dot_ratio`). Encode uses it when those options are omitted. An explicit flag overrides one field and leaves the rest of the profile in place.

Printing talks IPP directly. If the printer answers plain IPP with HTTP 426 and asks for TLS, the same request is retried as IPPS. The job ticket is color, single-sided unless `--duplex` is set, `print-quality` high when the printer lists it, `print-scaling=none`, and a `media-col` whose margins are the smallest positive value the printer advertises (never zero). The feed is `main` (the cassette) when that source exists, otherwise another tray or `auto`. Rear, photo, and manual feeds are not chosen. The document is PWG raster when the printer offers it, otherwise JPEG. Vendor page-description languages are not sent. `ipp-attribute-fidelity` is set, and a ticket the printer will not accept is refused before a job is submitted. `--duplex` sends one Print-Job with `sides=two-sided-long-edge` when the printer lists it, and `two-sided-short-edge` when that is the only duplex mode. Pages stay in encoded order, paired onto sheets, and a final odd page is the last side. The print fails if the printer does not advertise duplex or cannot put both sides in one PWG document. The TUI Print screen has the same duplex control, off by default.

Scanning talks eSCL over HTTP or HTTPS. The scan is RGB JPEG of the platen at the requested resolution, or the closest resolution the scanner lists. SANE is used only on Linux, and only when the selected device id is not an `http` or `https` URI.

---

## Project layout

| Path | Role |
|------|------|
| `src/main.py` | Logging and Typer entry |
| `src/cli/` | Commands, Rich output, `cli/tui/` screens |
| `src/common/` | Config, codec, compression, crypto, IPP/eSCL, optional CUPS/SANE, layouts, types |
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

One layout. The printed page carries every parameter the decoder needs. Defaults target an Epson ET-8500 used with Epson’s own driver at about **720 dpi**: **A4**, **5 mm** margins, **22 px** cells (about 0.78 mm), a **5-symbol** alphabet, **4 mm** AprilTags at a **16 mm** pitch, and **25%** Reed–Solomon redundancy. The QR module stays **0.36 mm**. On this printer the calibration reads cells down to 13 px and AprilTags down to 5 mm. Cell size, alphabet (5, 8, or 11), and dpi are configurable. Cells must be at least **0.49 mm** (14 px at 720 dpi).

### Header

The QR payload is the base64 of a **78-byte** big-endian record (74-byte body plus CRC-32). QR code **version 10**, error correction **H**, **4** quiet-zone modules, module size **0.36 mm**, drawn at its native module size.

| Field | Width | Meaning |
| --- | --- | --- |
| magic | 4 | `PCLP` |
| tag_pitch_mm | 1 | AprilTag pitch in whole millimetres (default 16) |
| flags | 1 | bit 0: user passphrase. Bits 1–3: AprilTag scale index. Index 0 is 8.0 mm, so older pages stay valid |
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

`ecc_sym` is `ceil(200 × redundancy)`. The default redundancy **0.25** stores **50** parity symbols. Each block is **200** data bytes and a **250**-byte codeword (`min(200, 255 − ecc_sym)` data bytes). The byte codec corrects 25 errors, or up to 50 erasures, per block. The decoder uses `ecc_sym` from the header.

### Page

Usable area is the page inside the margins, snapped to the cell grid. Every margin is rounded up to whole cells, so the printed margin is never below the requested one (5 mm becomes 5.43 mm at 22 px / 720 dpi).

The QR header sits at the **centre** of the page. It reserves one rectangular keep-out block, aligned to the cell grid:

- **QR code**: `ceil(qr_side / cell)` cells square, including its 4-module quiet zone. The block is placed so the QR centre falls within one cell of the page centre.
- **Calibration strip**: directly under the QR, horizontally centred: two rows of `num_symbols` colour cells. It is adjacent to the QR so both share the same well-supported part of the dewarp.
- **One blank cell row** under the strip, separating it from the data dots.
- The block is `max(qr_cells, num_symbols + 2)` cells wide and `qr_cells + 3` cells tall.

Data cells tile the rest of the usable area, row-major from the top-left. Only the centre block and the tag quiet zones are excluded. There is no header band.

AprilTag **36h11** marks form a regular mesh over the whole usable area. The default tag is **8 mm** with a **1.8 mm** quiet zone. Bits 1–3 of `flags` select a smaller scale: 8, 6, 5, 4, 3.5, 3, 2.5, or 2 mm. The quiet zone scales with the tag. The pitch byte still sets how many tags fit: at least the tag plus both quiet zones, and at least `tag_pitch_mm`. The grid is 2–5 columns and 2–6 rows, and the tag id is always `row × columns + column`.

`paper-clip calibrate sheet` renders one duplex A4 sheet. A frame of 8 mm AprilTags locates the page, and every other patch tests one thing: QR module size, AprilTag size, tag pitch, cell pitch, dot diameter, or symbol count. Each patch has a 3 × 2 mesh of its own tags, and its dots are read through them. FRONT and BACK are printed at the top of each side. The front carries the coarser sweep. The back spends the second face on finer probes: QR 0.18 mm, AprilTag 2 mm, tag pitch 12 mm, cells 16, 15, 14, and 13 px, and 8- and 11-symbol patches at 17 px and those smaller cells. A passing 12 mm pitch is reported in the limit table and is not written into the profile. The saved cell is one step larger than the smallest cell that passed, and it has to be at least 0.49 mm. The pitch choice stays on 16, 24, and 32 mm.

The calibration is a guided session, in the TUI **Calibrate** panel or on the command line:

1. `calibrate sheet` renders the sheet and checks that the clean pages read perfectly.
2. `calibrate simulate` (optional) runs the ink model at strengths 0.3, 0.6, and 1.0. It does not print or save a profile.
3. `calibrate print` shows the printer, asks once, and sends one duplex job. It never retries.
4. `calibrate scan` asks for the front and then the back. Either orientation is read as-is: the side and rotation are detected, so the sheet does not need to be turned around on the glass. Reads are cached next to each scan.
5. `calibrate save` shows the current profile beside the new one and asks before saving.

`calibrate status` shows the steps, the next instruction, and the limit table. `calibrate new` archives the session scans so a new sheet starts clean. A size counts only when it and every larger size passed; the saved profile is one step back from the smallest of those. An AprilTag size passes when at least 95% of its tags are found, the tag mesh predicts each held-out tag to within 0.4 cell, and its dots read at 99% or better with no row or column slip. Data printing stays one-sided unless `paper-clip print --duplex` or the TUI Print duplex control is on. Calibration duplexes when the printer can put both sides in one PWG document. Flag bits 4–6 select the QR module (0.36 mm when unset). The high 4 bits of the cell-size field select the dot ratio (0.62 when unset).

A tag whose quiet zone would touch the centre block is moved by the smallest horizontal or vertical step that clears it. The step is at most 0.75 of the tag pitch, and the moved tag must stay inside the usable area without touching another tag. A tag is skipped only when no such move exists. Ids never change, so the mesh stays deterministic. On default A4 no tag needs to move; on the A6 test page tags 12 and 17 move up 7.6 mm and down 11.4 mm. Corner tags are never affected. Tags are drawn last, and each quiet zone is snapped onto the cell grid so it does not cut a neighbouring dot. Dots use **0.62** of the cell and do not touch.

Default A4 layout (page coordinates from the top-left corner, in mm; the annotated render comes from `scripts/render_example_page.py`):

| Element | x | y | Size |
| --- | --- | --- | --- |
| Data area (inside margins) | 5.64 | 5.64 | 198.68 × 285.61 |
| Centre keep-out block | 93.70 | 136.60 | 23.71 × 27.09 |
| QR code with quiet zone | 94.09 | 136.98 | 22.93 × 22.93 |
| Calibration strip | 102.73 | 160.30 | 5.64 × 2.26 |
| Tags | 30 of 6 × 5 | | 7.76 square, 1.8 quiet zone |

The default A4 page (720 dpi, 22 px cells, 4 mm tags, 5 mm margins, 5 symbols) has **91,748** data cells and holds **26,208 bytes**. At the A6 test settings (360 dpi, 18 px cells, 10 mm margins, 5 symbols) the page is 1488×2098 px, the mesh is **6×5** tags, and the capacity is **3,620 cells / 1,032 bytes** (formerly 774). The same A6 page with 5 mm margins holds 1,428 bytes.

### Margins and borderless printing

paper-clip pages are **never printed borderless**. Borderless printing sprays ink past the paper edge onto the absorber pads and platen, which wears the printer and soils it inside. The format refuses to lay out a page in that territory.

- Epson's ET-8500/ET-8550 User's Guide, *Printable Area Specifications* ([PDF](https://files.support.epson.com/docid/cpd5/cpd59879.pdf), [online](https://download4.epson.biz/sec_pubs/et-8500_series/useg/en/GUID-5EAA5A0B-C8EA-46EF-81A2-14A73CC74FEB.htm)), gives **3 mm (0.12 in)** as the minimum top, bottom, left and right margin for single sheets printed with borders.
- `format_spec.MIN_MARGIN_MM` is that **3 mm plus a 1 mm safety allowance = 4 mm**, for feed skew and driver rounding. `resolve_config` and header parsing reject any margin below it, so neither the encoder nor a crafted header can request a borderless layout.
- The default is **5 mm** (`DEFAULT_MARGIN_MM`). Moving from 12 mm to 5 mm adds about 14% capacity on A4; going down to the 4 mm floor would add only about 2% more.
- Print at 100% / actual size, with borderless off. `paper-clip print` asks the printer for that directly: `print-scaling=none`, a positive `media-col` margin, and cassette (`main`) feed when the printer advertises it. When printing from the rear paper feed slot, Epson cannot print within 20 mm of the bottom edge, so use the cassette or set a 20 mm bottom margin. Epson also marks the top 41 mm and bottom 37 mm as areas where quality can drop; the tag mesh and Reed–Solomon parity absorb that.

### Payload and parity

The file is compressed with Zstandard and encrypted with Argon2id + AES-GCM. A built-in key is used when no passphrase is given. Inside the Reed–Solomon stream, three copies of a 7-byte header (`uint32` blob length, `uint16` block count, `uint8` filename length) precede the filename and the ciphertext. Copies are majority-voted on decode.

Optional parity pages are a second Reed–Solomon code along the page axis: one symbol per byte position, short pages zero-padded, `total_pages − data_pages` parity symbols. If decryption, the SHA-256, or the byte code fails and a parity page is present, the decoder drops the data page with the most erasures and rebuilds that page.

### Decode and tests

`paper-clip decode` loads a scan, reads the QR header, finds the tag grid, and dewarps the page. A homography pinned to the corner tags and the QR corners carries the perspective. A thin-plate spline fitted to the residual at every detected tag and QR corner carries the paper curl, so missing tags only thin the fit and do not open holes. If the QR does not decode directly, the decoder locates it and retries a few small quadratic bends of the crop, which recovers a centred QR on a strongly curled page. Cells are sampled on the dewarped grid. Colour classification uses a mild unsharp mask (amount 0.75, sigma 0.7 px) and a median of radius `dot_radius / 4`. A saved TensorFlow 2 network is used when `models/cell_decoder.keras` is present; otherwise, or with `--no-model`, classification is nearest-colour in Lab against the calibration strip. Low confidence becomes Reed–Solomon erasures. Then decrypt, decompress, reassemble, and check the original SHA-256.

`uv run pytest` runs the fast suite. `uv run python scripts/sweep_decode.py` reports success, pre-RS symbol error, erasures, and decode time across strengths, payload sizes, and both decoders (20 fixed-seed samples by default; the protocol page is A6 with 10 mm margins, and `--margin-mm` sweeps other margins). `uv run python scripts/render_example_page.py` renders the largest random payload that fits one default A4 page, an annotated copy, and checks that the page decodes. `uv run python scripts/train_cell_decoder.py` retrains the cell decoder on the synthetic photometric model. `uv run python scripts/train_cell_decoder.py SCAN_DIR DIGITAL_DIR` labels a scanned print from the digital pages that were sent to the printer and retrains on those cells.

---

## Python dependencies

Core dependencies are declared in `pyproject.toml` and pinned in `uv.lock`.

Hardware discovery integrations are optional and installed with:

```bash
uv sync --extra hardware
```

This extra includes `pycups` on macOS and Linux, and `python-sane` on Linux. Building those packages needs the system headers (`libcups2-dev` and `libsane-dev` on Debian). The core install does not. The TensorFlow cell decoder is installed on Linux and on Apple Silicon. An Intel Mac still encodes, prints, scans, and decodes with nearest-colour classification.
