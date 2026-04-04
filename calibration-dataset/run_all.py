import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _run(cmd: list[str], desc: str) -> None:
    print(f"\n{'=' * 60}\n{desc}\n{'=' * 60}")
    r = subprocess.run(cmd, cwd=str(ROOT), check=False)
    if r.returncode != 0:
        raise SystemExit(f"Step failed ({r.returncode}): {' '.join(cmd)}")


def main() -> None:
    p = argparse.ArgumentParser(description="Run calibration ML pipeline end-to-end")
    p.add_argument(
        "--skip-align",
        action="store_true",
        help="Skip align.py (use existing output/aligned/)",
    )
    p.add_argument(
        "--skip-train",
        action="store_true",
        help="Skip train_cnn.py (only build dataset and evaluate if models exist)",
    )
    p.add_argument(
        "--epochs",
        type=int,
        default=None,
        help="Epochs for train_cnn (default: value in train_cnn.py)",
    )
    p.add_argument(
        "bands",
        nargs="*",
        type=int,
        default=None,
        help="Optional band sizes for training only; default all bands",
    )
    args = p.parse_args()

    uv = "uv"
    py = [uv, "run", "python"]

    if not (ROOT / "ground_truth.json").exists():
        _run(py + ["parse_ground_truth.py"], "Phase 1: parse ground truth")

    if not args.skip_align:
        _run(py + ["align.py"], "Phase 2–3: corner detection + align scans")

    _run(py + ["extract_dots.py"], "Phase 4: extract dots + sample montages")

    _run(py + ["build_dataset.py"], "Phase 5: build TFRecords")

    if not args.skip_train:
        train_cmd = py + ["train_cnn.py"]
        if args.epochs is not None:
            train_cmd.extend(["--epochs", str(args.epochs)])
        if args.bands:
            train_cmd.extend([str(b) for b in args.bands])
        _run(train_cmd, "Phase 6: train CNNs per band")

    _run(py + ["evaluate_pipeline.py"], "Phase 6: evaluate pipeline")

    print("\nPipeline finished.")


if __name__ == "__main__":
    main()
