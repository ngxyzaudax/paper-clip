# paper-clip

Serialize files to **physical paper** as high-resolution PNGs: a color-coded dot grid carries compressed, error-corrected data with QR headers and calibration marks. Optional encryption and page-level parity are supported. The local web interface and the CLI cover **encoding**, **printing**, **scanning**, **decoding**, and **hardware discovery**.

- **Python:** 3.13+ (see `.python-version`), on macOS or Linux
- **Web:** run `paper-clip` with **no arguments** to serve the interface on `127.0.0.1` and open it. `paper-clip serve --port 8765 --host 127.0.0.1 --no-browser` changes the bind. A host other than loopback prints a one-time bearer token and refuses requests without it.
- **CLI:** [Typer](https://typer.tiangolo.com/) — `encode`, `decode`, `print`, `scan`, `devices`, `health`, and `calibrate` stay headless for automation.

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
| `encode` | File → PNG page(s) |
| `decode` | Scanned PNG/JPEG/TIFF, a directory, or a scan job → original file, plus a paper health reading. An existing file is kept, and the new one is saved as `name (1).ext`, unless `--force` is given. `--no-track` skips the health history |
| `health` | Paper health of every tracked file. `health show NAME` for the trend, advice, zone map, and past checks; `health check SCAN` rates the paper without writing the file; `health forget NAME`; `--open` opens the damage image |
| `print` | PNG page(s) → IPP Everywhere job (bordered, 100% scale, color; one-sided unless `--duplex`) |
| `scan` | One eSCL platen scan → JPEG or PNG |
| `devices` | IPP / eSCL discovery and the safe print ticket |
| `calibrate` | One duplex sheet that measures QR, AprilTag, dot, and symbol limits separately |

Use `uv run paper-clip <command> --help` for flags, or run `paper-clip` with no arguments for the web interface. It opens on Home, which shows the newest job of each step, paper health alerts, devices, and quick actions. The rail follows the workflow: Encode, Print, Scan and decode, then Health, Devices, and Calibrate. `Cmd+K` jumps to a view or job, and `?` lists the shortcuts. After an encode, Print opens that job. After printing, Scan and decode continues it. Decode saves to `data/decoded/<job>/` without overwriting, shows the paper health, and links to the file's history. The web app is built from `web/` (`npm ci` and `npm run build`); `web/dist` is what `paper-clip` serves. A dev server can proxy `/api` to port 8765.

### Paper health

Every decode also rates the paper. Each Reed–Solomon block can absorb `ecc_sym` units of damage: an erasure (a cell the reader flagged as unsure) costs one, a silent wrong byte costs two. Health is the share of that budget still unused in the weakest block, so 100% is untouched paper and 0% means the next damaged byte loses data. A page that had to be rebuilt from page parity caps health at 35% (15% when no spare parity page is left). A scan whose header still reads but whose data no longer decodes is recorded as **Lost** at 0%. Bands: **Healthy** 60% and up, **Worn** 35–60%, **At risk** 15–35%, **Critical** below 15%.

Readings are kept per file (keyed by the original SHA-256) in `data/health/<sha256>.json`, with the change since the last check, the yearly rate once checks span a day, and the date the paper reaches the reprint level at that rate. Each check also writes `data/health/damage/<id>/<time>.png`: every scanned page rectified, faded, with misread cells in red and cells the reader doubted but got right in orange. Misread cells are found by re-encoding the corrected bytes and comparing them with what the reader saw, so a marker stroke shows up as the exact cells it covered. Printing a job or the calibration sheet always asks first. The print stays single-sided unless duplex is switched on.

### Driverless printing and scanning

`paper-clip devices` browses mDNS for `_ipp._tcp`, `_ipps._tcp`, and `_uscan._tcp`. Queries go out from each IPv4 interface on its own ephemeral port, which is where the unicast reply comes back. A second socket listens on UDP port 5353 for multicast replies. macOS shares that port with mDNSResponder. Linux shares it with Avahi without `SO_REUSEPORT`, because that option would hand each multicast packet to only one listener. Saved device URIs use the literal address from the reply, so Linux does not need `nss-mdns` to resolve `.local`. A saved `printer.uri` or `scanner.uri` in `data/devices.json` is used as well. `printer.profile` stores the density calibration (`cell_size_px`, `num_symbols`, `tag_size_mm`, `tag_pitch_mm`, `print_dpi`, `qr_module_mm`, `dot_ratio`). Encode uses it when those options are omitted. An explicit flag overrides one field and leaves the rest of the profile in place.

Printing talks IPP directly. If the printer answers plain IPP with HTTP 426 and asks for TLS, the same request is retried as IPPS. The job ticket is color, single-sided unless `--duplex` is set, `print-quality` high when the printer lists it, `print-scaling=none`, and a `media-col` whose margins are the smallest positive value the printer advertises (never zero). The feed is `main` (the cassette) when that source exists, otherwise another tray or `auto`. Rear, photo, and manual feeds are not chosen. The document is PWG raster when the printer offers it, otherwise JPEG. Vendor page-description languages are not sent. `ipp-attribute-fidelity` is set, and a ticket the printer will not accept is refused before a job is submitted. `--duplex` sends one Print-Job with `sides=two-sided-long-edge` when the printer lists it, and `two-sided-short-edge` when that is the only duplex mode. Pages stay in encoded order, paired onto sheets, and a final odd page is the last side. The print fails if the printer does not advertise duplex or cannot put both sides in one PWG document. The Print view has the same duplex control, off by default.

Scanning talks eSCL over HTTP or HTTPS. The scan is RGB JPEG of the platen at the requested resolution, or the closest resolution the scanner lists. SANE is used only on Linux, and only when the selected device id is not an `http` or `https` URI.

---

## Project layout

| Path | Role |
|------|------|
| `src/main.py` | Logging and Typer entry |
| `src/cli/` | Headless Typer commands and Rich output |
| `src/workflows/` | Shared job, encode, decode, scan, print, and calibrate steps |
| `src/web/` | Local FastAPI app, previews, and the scan-and-decode wizard |
| `web/` | React interface |
| `src/common/` | Config, codec, compression, crypto, IPP/eSCL, optional CUPS/SANE, layouts, types |
| `src/serialization/encode/` | Encoder, QR header, calibration strip, tag grid |
| `src/serialization/decode/` | QR, AprilTag mesh dewarp, cell classification, RS, decrypt |
| `src/health/` | Paper health from RS repair use, history store, trend, damage images |
| `src/ml/` | TensorFlow 2 cell decoder, synthetic trainer, saved-model loading |
| `src/scan_sim/` | Shared print/scan augmentation used by tests and training |
| `models/cell_decoder.keras` | Synthetic cell decoder shipped with the repo |
| `scripts/sweep_decode.py` | Heavier decode success-rate sweep |
| `tests/` | Fast pytest subset (`pytest`, skips `slow`) |

Runtime data lives under **`data/`**: `print/jobs/`, `scan/jobs/`, `decoded/`, `health/`, `calibration/`, `inbox/`, and `.thumbs/`.

---

## Format

One layout. The printed page carries every parameter the decoder needs. Defaults target an Epson ET-8500 used with Epson’s own driver at about **720 dpi**: **A4**, **5 mm** margins, **22 px** cells (about 0.78 mm), a **5-symbol** alphabet, **4 mm** AprilTags at a **16 mm** pitch, and **50** Reed–Solomon parity bytes. The QR module stays **0.36 mm**. On this printer the calibration reads 11 symbols down to 10 px and AprilTags down to 5 mm. Cell size, alphabet (5, 8, or 11), and dpi are configurable. Cells must be at least **0.35 mm** (10 px at 720 dpi).

### Header

The QR payload is the base64 of a **78-byte** big-endian record (74-byte body plus CRC-32). QR code **version 10**, error correction **H**, **4** quiet-zone modules, module size **0.36 mm**, drawn at its native module size.

| Field | Width | Meaning |
| --- | --- | --- |
| magic | 4 | `PCLP` |
| tag_pitch_mm | 1 | AprilTag pitch in whole millimetres (default 16) |
| flags | 1 | bit 0: user passphrase. Bits 1–3: AprilTag scale, 8.0 mm to 2.0 mm. Bits 4–6: QR module scale, 0.36 mm to 0.18 mm |
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

`ecc_sym` is the parity-byte count, from **2** to **254**. The default is **50**. Each block keeps **200** data bytes until parity exceeds 55, then the data side shrinks so the codeword stays at most **255** bytes (`min(200, 255 − ecc_sym)` data bytes). At 50 parity bytes the codeword is **250** bytes and corrects 25 errors, or 50 erasures. The encoder may raise the count to fill the pages the file already needs, and it never adds a page to do so. The decoder uses `ecc_sym` from the header.

### Page

Usable area is the page inside the margins, snapped to the cell grid. Every margin is rounded up to whole cells, so the printed margin is never below the requested one (5 mm becomes 5.43 mm at 22 px / 720 dpi).

The page carries **four identical QR copies**, not one code in the middle. Each copy has its own keep-out block, aligned to the cell grid. Each block is centred in the open cell of the AprilTag mesh nearest its quadrant, with the same gap on every side. On default A4 that gap is about **15 mm**. On the saved printer profile (13 px cells, 11 symbols, 6 mm tags) it is about **20 mm**.

- **QR code**: `ceil(qr_side / cell)` cells square, including its 4-module quiet zone.
- **Calibration strip**: directly under that QR: two rows of `num_symbols` colour cells, so each copy can be colour-checked on its own.
- **One blank cell row** under the strip, separating it from the data dots.
- The block is `max(qr_cells, num_symbols + 2)` cells wide and `qr_cells + 3` cells tall. The four blocks do not overlap.

The same 78-byte header is also written into the dot grid. It is a Reed–Solomon codeword with **64** parity bytes, stored **twice** (284 bytes, 1,008 cells on a 5-symbol page). Those cells are spread through the usable area, outside the header blocks and the tag quiet zones. The file uses only the remaining cells. One intact copy is enough to recover the header when every QR is unreadable.

Data cells are the rest of that usable area, row-major from the top-left.

AprilTag **36h11** marks form a regular mesh over the whole usable area. Bits 1–3 of `flags` select the tag scale: 8, 6, 5, 4, 3.5, 3, 2.5, or 2 mm. An 8 mm tag has a **1.8 mm** quiet zone, and the quiet zone scales with the tag. The shipped default is **4 mm**, so the quiet zone is about **0.92 mm**. The pitch byte still sets how many tags fit: at least the tag plus both quiet zones, and at least `tag_pitch_mm`. The grid is 2–5 columns and 2–6 rows, and the tag id is always `row × columns + column`.

`paper-clip calibrate sheet` renders one duplex A4 sheet. A frame of 8 mm AprilTags locates the page. Each probe is a 3 × 2 tag mesh whose pitch grows until the tags and their quiet zones meet the edges of the slot, and the slots tile the content box. The front keeps two sizes coarser than the last full pass, then the pass itself: QR modules 0.25, 0.22, and 0.20 mm, tags 8, 6, and 5 mm, and cells 15, 14, and 13 px. The back fills the second face with cells 12, 11, 10, 9, and 8 px. Every cell is printed at dot ratios 0.50, 0.62, and 0.75, with an 11-symbol patch at the 0.62 ratio so a pass cannot be saved as 5 symbols. Sizes that already failed, or that the ink cannot form, are not printed: QR at 0.18 mm and below, tags of 4 mm and below, and cells of 7 px and below. The saved cell is the smallest passing size whose symbol read stays within half a percentage point of the larger passing sizes, and at least 0.35 mm. QR module and AprilTag size stay one step short of the tightest size that passed. Tag pitch stays 16 mm.

The calibration is a guided session, in the **Calibrate** view or on the command line:

1. `calibrate sheet` renders the sheet and checks that the clean pages read perfectly.
2. `calibrate simulate` (optional) runs the ink model at strengths 0.3, 0.6, and 1.0. It does not print or save a profile.
3. `calibrate print` shows the printer, asks once, and sends one duplex job. It never retries.
4. `calibrate scan` asks for the front and then the back. Either orientation is read as-is: the side and rotation are detected, so the sheet does not need to be turned around on the glass. Reads are cached next to each scan.
5. `calibrate save` shows the current profile beside the new one and asks before saving.

`calibrate status` shows the steps, the next instruction, and the limit table. `calibrate new` archives the session scans so a new sheet starts clean. A size counts only when it and every larger size passed; the saved profile is one step back from the smallest of those. An AprilTag size passes when at least 95% of its tags are found, the tag mesh predicts each held-out tag to within 0.4 cell, and its dots read at 99% or better with no row or column slip. Data printing stays one-sided unless `paper-clip print --duplex` or the Print view duplex control is on. Calibration duplexes when the printer can put both sides in one PWG document. Flag bits 4–6 select the QR module (0.36 mm when unset). The high 4 bits of the cell-size field select the dot ratio (0.62 when unset).

The target air between a header block and a tag quiet zone is **3 mm**. A tag that would overlap a block is moved by the smallest horizontal or vertical step that opens that gap. The step is at most 0.75 of the tag pitch, and the moved tag must stay inside the usable area without touching another tag. When the pitch limit is reached first, the tag moves as far as the limit allows. A tag is skipped only when no move fits. Ids never change, so the mesh stays deterministic. Default A4 leaves about 15 mm, so no tag has to move. On the A6 test page the QR block is wider than the gap between tags, so the block stays on the quadrant and the nearby tags step aside. With 10 mm margins, tags 6 and 8 move up 14.25 mm and tags 21 and 23 move down 14.25 mm, leaving about 1.6 mm to 2.2 mm of air. With 5 mm margins the same four tags move, 6 and 8 up 15.10 mm and 21 and 23 down 14.46 mm, and the air is the full 3 mm. Corner tags stay put. Tags are drawn last, and each quiet zone is snapped onto the cell grid so it does not cut a neighbouring dot. Dots use **0.62** of the cell and do not touch.

Default A4 layout (page coordinates from the top-left corner, in mm; the annotated render comes from `scripts/render_example_page.py`):

| Element | x | y | Size |
| --- | --- | --- | --- |
| Data area (inside margins) | 5.43 | 5.43 | 198.68 × 285.61 |
| Header block, top left | 20.95 | 79.16 | 23.28 × 25.61 |
| Header block, top right | 165.31 | 79.16 | 23.28 × 25.61 |
| Header block, bottom left | 20.95 | 190.92 | 23.28 × 25.61 |
| Header block, bottom right | 165.31 | 190.92 | 23.28 × 25.61 |
| QR inside the top-left block | 21.13 | 79.34 | 22.93 × 22.93 |
| Calibration strip under that QR | 30.27 | 102.45 | 3.88 × 1.55 |
| Tags | 30 of 6 × 5 | | 3.88 square, 0.92 quiet zone |

The other three QRs and strips sit inside their blocks the same way. The default A4 page (720 dpi, 22 px cells, 4 mm tags, 5 mm margins, 5 symbols) has **87,407** data cells and holds **24,972 bytes**. The in-grid header uses another **1,008** cells. Dots that would touch a header block or a tag quiet zone are left unused, so a half-pixel dewarp still samples ink. At the A6 test settings (360 dpi, 18 px cells, 10 mm margins, 5 symbols) the page is 1488×2098 px, the mesh is **6×5** tags, and the capacity is **3,160 cells / 900 bytes**. The same A6 page with 5 mm margins holds **1,302 bytes**.

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

`paper-clip decode` loads a scan, reads any of the four QR copies, finds the tag grid, and dewarps the page. A homography pinned to the corner tags, with matching QR corners as extra anchors, carries the perspective. A thin-plate spline fitted to the residual at every detected tag and matched QR corner carries the paper curl, so missing tags only thin the fit and do not open holes. If a QR does not decode directly, the decoder searches the page and retries a few small quadratic bends of the crop. When no QR reads, it warps from the tags using a header from another page of the same scan, or from a recent print job, and reads the in-grid header copy. A page that loses every QR and the in-grid copy is still read from a sibling header and placed in a missing page index when the document checksum accepts that assignment. Colour calibration samples every strip, drops a strip whose score is more than 15 Lab units worse than the best, and averages the rest. Cells are sampled on the dewarped grid. Colour classification uses a mild unsharp mask (amount 0.75, sigma 0.7 px) and a median of radius `dot_radius / 4`. A saved TensorFlow 2 network is used when `models/cell_decoder.keras` is present; otherwise, or with `--no-model`, classification is nearest-colour in Lab against the calibration strip. Low confidence becomes Reed–Solomon erasures. Then decrypt, decompress, reassemble, and check the original SHA-256.

`uv run pytest` runs the fast suite. `uv run python scripts/sweep_decode.py` reports success, pre-RS symbol error, erasures, and decode time across strengths, payload sizes, and both decoders (20 fixed-seed samples by default; the protocol page is A6 with 10 mm margins, and `--margin-mm` sweeps other margins). `uv run python scripts/render_example_page.py` renders the largest random payload that fits one default A4 page, an annotated copy, and checks that the page decodes. `uv run python scripts/train_cell_decoder.py` retrains the cell decoder on the synthetic photometric model. `uv run python scripts/train_cell_decoder.py SCAN_DIR DIGITAL_DIR` labels a scanned print from the digital pages that were sent to the printer and retrains on those cells.

---

## Python dependencies

Core dependencies are declared in `pyproject.toml` and pinned in `uv.lock`.

Hardware discovery integrations are optional and installed with:

```bash
uv sync --extra hardware
```

This extra includes `pycups` on macOS and Linux, and `python-sane` on Linux. Building those packages needs the system headers (`libcups2-dev` and `libsane-dev` on Debian). The core install does not. The TensorFlow cell decoder is installed on Linux and on Apple Silicon. An Intel Mac still encodes, prints, scans, and decodes with nearest-colour classification.
