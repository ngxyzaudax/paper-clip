import argparse
from pathlib import Path

import numpy as np

from common.config import resolve_config
from scan_sim import apply_scan_augment
from serialization.decode.errors import DecodeError
from serialization.decode.pipeline import decode
from scan_sim.render import render_arrays


def main() -> None:
    parser = argparse.ArgumentParser(description="Decode success rate across synthetic scan strengths.")
    parser.add_argument("--samples", type=int, default=4)
    parser.add_argument("--strengths", type=float, nargs="+", default=[0.0, 0.25, 0.5, 0.75, 1.0])
    parser.add_argument("--bytes", type=int, default=180)
    parser.add_argument("--use-model", action="store_true")
    args = parser.parse_args()
    config = resolve_config(paper_size="A6", print_dpi=360, cell_size_px=18, margin_mm=10)
    print(f"{'strength':>10} {'ok':>6} {'rate':>8}")
    for strength in args.strengths:
        ok = 0
        for index in range(args.samples):
            rng = np.random.default_rng(10_000 + index * 17 + int(strength * 1000))
            payload = rng.integers(0, 256, size=args.bytes, dtype=np.uint8).tobytes()
            pages = render_arrays(payload, config, filename=f"sweep-{index}.bin")
            scans = [
                apply_scan_augment(page, strength, config.print_dpi, np.random.default_rng(rng.integers(1, 1_000_000_000)))
                for page in pages
            ]
            try:
                recovered, _name = decode(scans, use_model=True if args.use_model else False)
                ok += int(recovered == payload)
            except DecodeError:
                ok += 0
        rate = ok / args.samples if args.samples else 0.0
        print(f"{strength:10.2f} {ok:6d} {rate:8.1%}")


if __name__ == "__main__":
    main()
