#!/usr/bin/env python3
"""Roundtrip encode/decode verification for all config profiles."""

import sys
import tempfile
import time
from pathlib import Path

import numpy as np

from common.config import load_config
from common.page_layout import data_capacity_bytes
from common.symbols import bits_per_cell
from serialization.decode.pipeline import decode
from serialization.encode.pipeline import render_pages

CONFIGS_DIR = Path("data/configs")
DEFAULT_TEST_FILE = Path("shannon.jpg")


def run_profile_test(profile_path: Path, test_file: Path) -> tuple[str, bool, str]:
    name = profile_path.stem
    try:
        config = load_config(profile_path)
    except Exception as exc:
        return name, False, f"config load failed: {exc}"

    original = test_file.read_bytes()
    cap = data_capacity_bytes(config)
    bpc = bits_per_cell(config.num_colors)

    t0 = time.perf_counter()
    images = render_pages(test_file, config)
    t_enc = time.perf_counter() - t0

    bgr_images = [np.array(img.convert("RGB"))[:, :, ::-1] for img in images]

    with tempfile.TemporaryDirectory() as tmp:
        t1 = time.perf_counter()
        try:
            result, filename = decode(bgr_images, Path(tmp) / "out")
        except Exception as exc:
            return name, False, f"decode error: {exc}"
        t_dec = time.perf_counter() - t1

    match = result == original
    detail = (
        f"{config.num_colors}c "
        f"cell={config.cell_size_px}px "
        f"bpc={bpc:.2f} "
        f"pages={len(images)} "
        f"cap={cap / 1024:.1f}KB "
        f"enc={t_enc:.1f}s dec={t_dec:.1f}s "
        f"fname={filename or '-'}"
    )
    return name, match, detail


def main() -> None:
    test_file = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TEST_FILE
    if not test_file.exists():
        print(f"Test file not found: {test_file}", file=sys.stderr)
        sys.exit(1)

    profiles = sorted(CONFIGS_DIR.glob("*.toml"))
    if not profiles:
        print(f"No profiles found in {CONFIGS_DIR} (add .toml profiles under data/configs)")
        sys.exit(0)

    print(f"Testing {len(profiles)} profile(s) with {test_file} ({test_file.stat().st_size:,} bytes)\n")

    passed = 0
    failed = 0
    for profile_path in profiles:
        name, ok, detail = run_profile_test(profile_path, test_file)
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name:<14} {detail}")
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\n{passed}/{passed + failed} passed", end="")
    if failed:
        print(f", {failed} failed")
        sys.exit(1)
    print()


if __name__ == "__main__":
    main()
