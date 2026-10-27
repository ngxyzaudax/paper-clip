import argparse
import json
from pathlib import Path

from scan_sim.sweep import PROTOCOL_BYTES, PROTOCOL_DECODERS, PROTOCOL_SAMPLES, PROTOCOL_STRENGTHS, SweepRow, run_sweep


def main() -> None:
    parser = argparse.ArgumentParser(description="Decode success, symbol error, erasures, and runtime.")
    parser.add_argument("--samples", type=int, default=PROTOCOL_SAMPLES)
    parser.add_argument("--strengths", type=float, nargs="+", default=list(PROTOCOL_STRENGTHS))
    parser.add_argument("--bytes", type=int, nargs="+", default=list(PROTOCOL_BYTES))
    parser.add_argument("--decoders", nargs="+", choices=["colour", "model", "both"], default=["both"])
    parser.add_argument("--model", type=Path, default=None)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()
    decoders = _decoders(args.decoders)
    rows: list[SweepRow] = []
    _print_header()
    run_sweep(
        samples=args.samples,
        strengths=tuple(args.strengths),
        sizes=tuple(args.bytes),
        decoders=decoders,
        model_path=str(args.model) if args.model else None,
        on_row=lambda row: _collect(rows, row),
    )
    if args.json is not None:
        args.json.write_text(json.dumps([row._asdict() for row in rows], indent=2) + "\n")


def _decoders(names: list[str]) -> tuple[str, ...]:
    if "both" in names:
        return PROTOCOL_DECODERS
    ordered = [name for name in PROTOCOL_DECODERS if name in names]
    return tuple(ordered)


def _collect(rows: list[SweepRow], row: SweepRow) -> None:
    rows.append(row)
    _print_row(row)


def _print_header() -> None:
    print(
        f"{'strength':>8} {'bytes':>6} {'decoder':>8} {'ok':>8} {'success':>8} "
        f"{'sym_err':>8} {'erasures':>9} {'located':>7} {'sec':>7}",
        flush=True,
    )


def _print_row(row: SweepRow) -> None:
    erasures = "nan" if row.located == 0 else f"{row.mean_erasures:.1f}"
    print(
        f"{row.strength:8.2f} {row.nbytes:6d} {row.decoder:>8} "
        f"{row.ok:3d}/{row.samples:<3d} {row.success_rate:8.1%} "
        f"{row.symbol_error_rate:8.1%} {erasures:>9} {row.located:7d} {row.mean_seconds:7.2f}",
        flush=True,
    )


if __name__ == "__main__":
    main()
