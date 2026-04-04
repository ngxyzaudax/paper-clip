from collections.abc import Callable
from pathlib import Path

from common.capture import run_capture_session
from common.config import FLAG_ENCRYPTED, ALGO_FIELDS
from common.config_store import load_profile
from common.data_store import create_job, digital_dir, find_job, load_job_metadata, update_job_metadata
from common.page_layout import data_capacity_bytes
from serialization.encode.pipeline import encode


def prepare_generate_job(
    profile_name: str, pages: int, passphrase: str | None,
) -> tuple[Path, Path, str]:
    from common.test_data import generate_test_payload, save_test_file
    config = load_profile(profile_name)
    data = generate_test_payload(config, pages)
    config_dict = {k: getattr(config, k) for k in ALGO_FIELDS}
    job_dir = create_job(f"testdata_{pages}p", profile_name, config_dict, pages)
    test_path, sha256 = save_test_file(data, job_dir)
    update_job_metadata(job_dir, {
        "test_data": True, "original_sha256": sha256, "original_size": len(data),
    })
    return job_dir, test_path, sha256


def prepare_file_job(
    input_path: Path, profile_name: str,
) -> Path:
    config = load_profile(profile_name)
    file_size = input_path.stat().st_size
    total_pages = max(1, -(-file_size // data_capacity_bytes(config)))
    config_dict = {k: getattr(config, k) for k in ALGO_FIELDS}
    return create_job(input_path.name, profile_name, config_dict, total_pages)


def encode_job(
    input_path: Path, job_dir: Path, profile_name: str, passphrase: str | None,
) -> list[Path]:
    config = load_profile(profile_name)
    flags = FLAG_ENCRYPTED if passphrase else 0
    output_base = digital_dir(job_dir) / "page"
    return encode(input_path, output_base, config, flags=flags, passphrase=passphrase)


def run_capture(
    job_dir: Path,
    digital_pages: list[Path],
    profile_name: str,
    printer_name: str,
    scanner_device: str,
    scanner_dpi: int,
    scanner_mode: str,
    scans_count: int,
    on_status: Callable[[str], None] | None = None,
    on_prompt: Callable[[str], bool] | None = None,
) -> list[Path]:
    config = load_profile(profile_name)
    return run_capture_session(
        job_dir, digital_pages, printer_name,
        scanner_device, scanner_dpi, scanner_mode, scans_count,
        print_resolution=f"{config.scan_dpi}dpi",
        on_status=on_status, on_prompt=on_prompt,
    )


def run_full_capture(
    profile: str,
    printer: str,
    scanner_device: str,
    scanner_settings: dict,
    scans_per_page: int,
    passphrase: str | None,
    generate: bool,
    input_path: Path | None,
    generate_pages: int,
    resume_prefix: str | None = None,
    on_status: Callable[[str], None] | None = None,
    on_prompt: Callable[[str], bool] | None = None,
) -> str:
    resume = (resume_prefix or "").strip()
    if resume:
        job_dir = find_job(resume)
        if not job_dir:
            raise ValueError(f"No job found matching: {resume}")
        dpages = sorted((job_dir / "digital").glob("*.png"))
        if not dpages:
            raise ValueError("Job has no encoded pages in digital/")
        meta = load_job_metadata(job_dir)
        profile = str(meta.get("profile", profile))
        on_status and on_status(f"Resuming job {job_dir.name} ({len(dpages)} page(s))")
    elif generate:
        on_status and on_status("Generating test data...")
        job_dir, inp, sha = prepare_generate_job(profile, generate_pages, passphrase)
        on_status and on_status(f"Test: {sha[:24]}... Encoding...")
        dpages = encode_job(inp, job_dir, profile, passphrase)
    else:
        inp = input_path
        if inp is None:
            raise ValueError("Input file required")
        job_dir = prepare_file_job(inp, profile)
        on_status and on_status("Encoding...")
        dpages = encode_job(inp, job_dir, profile, passphrase)
    if resume:
        on_status and on_status(f"Starting capture for {len(dpages)} page(s)...")
    else:
        on_status and on_status(f"Encoded {len(dpages)} page(s). Starting capture...")
    masters = run_capture(
        job_dir, dpages, profile, printer, scanner_device,
        scanner_settings.get("dpi", 1200), scanner_settings.get("mode", "Color"),
        scans_per_page, on_status=on_status, on_prompt=on_prompt,
    )
    return f"[bold green]Done: {len(masters)} master(s) | Job: {job_dir}[/bold green]"
