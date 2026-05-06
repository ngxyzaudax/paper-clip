import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_ROOT = Path("data")
PRINT_JOBS_DIR = DATA_ROOT / "print" / "jobs"
SCAN_JOBS_DIR = DATA_ROOT / "scan" / "jobs"


def _generate_job_id(source_name: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = Path(source_name).stem.replace(" ", "_")[:40]
    return f"{stamp}_{stem}"


def create_print_job(
    source_filename: str,
    encoding_label: str,
    config_dict: dict,
    total_pages: int,
    *,
    paper_size: str,
    data_pages: int,
    payload_bytes: int,
    data_capacity_bytes_per_page: int,
) -> Path:
    job_id = _generate_job_id(source_filename)
    job_dir = PRINT_JOBS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "digital").mkdir(exist_ok=True)
    max_payload_bytes = data_capacity_bytes_per_page * data_pages
    metadata = {
        "job_id": job_id,
        "kind": "print",
        "source_file": source_filename,
        "encoding": encoding_label,
        "config": config_dict,
        "total_pages": total_pages,
        "paper_size": paper_size,
        "data_pages": data_pages,
        "payload_bytes": payload_bytes,
        "data_capacity_bytes_per_page": data_capacity_bytes_per_page,
        "max_payload_bytes_for_data_pages": max_payload_bytes,
        "created": datetime.now().isoformat(),
    }
    (job_dir / "job.json").write_text(json.dumps(metadata, indent=2))
    logger.info("Created print job %s at %s", job_id, job_dir)
    return job_dir


def create_scan_job(
    scanner_name: str,
    dpi: int,
    *,
    mode: str = "",
) -> Path:
    job_id = _generate_job_id("scan")
    job_dir = SCAN_JOBS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "scans").mkdir(exist_ok=True)
    metadata = {
        "job_id": job_id,
        "kind": "scan",
        "scanner_name": scanner_name,
        "dpi": dpi,
        "mode": mode,
        "created": datetime.now().isoformat(),
    }
    (job_dir / "job.json").write_text(json.dumps(metadata, indent=2))
    logger.info("Created scan job %s at %s", job_id, job_dir)
    return job_dir


def digital_dir(job_dir: Path) -> Path:
    d = job_dir / "digital"
    d.mkdir(parents=True, exist_ok=True)
    return d


def scans_dir(job_dir: Path) -> Path:
    d = job_dir / "scans"
    d.mkdir(parents=True, exist_ok=True)
    return d
