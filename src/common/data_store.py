import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_ROOT = Path("data")
JOBS_DIR = DATA_ROOT / "jobs"


def _generate_job_id(source_name: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = Path(source_name).stem.replace(" ", "_")[:40]
    return f"{stamp}_{stem}"


def create_job(
    source_filename: str,
    encoding_label: str,
    config_dict: dict,
    total_pages: int,
) -> Path:
    job_id = _generate_job_id(source_filename)
    job_dir = JOBS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "digital").mkdir(exist_ok=True)
    (job_dir / "scans").mkdir(exist_ok=True)
    metadata = {
        "job_id": job_id,
        "source_file": source_filename,
        "encoding": encoding_label,
        "config": config_dict,
        "total_pages": total_pages,
        "created": datetime.now().isoformat(),
    }
    (job_dir / "job.json").write_text(json.dumps(metadata, indent=2))
    logger.info("Created job %s at %s", job_id, job_dir)
    return job_dir


def digital_dir(job_dir: Path) -> Path:
    d = job_dir / "digital"
    d.mkdir(parents=True, exist_ok=True)
    return d
