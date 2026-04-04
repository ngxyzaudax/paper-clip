import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_ROOT = Path("data")
JOBS_DIR = DATA_ROOT / "jobs"
MODELS_DIR = DATA_ROOT / "models"
TRAINING_DIR = DATA_ROOT / "training"


def _generate_job_id(source_name: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = Path(source_name).stem.replace(" ", "_")[:40]
    return f"{stamp}_{stem}"


def create_job(
    source_filename: str,
    profile_name: str,
    config_dict: dict,
    total_pages: int,
) -> Path:
    job_id = _generate_job_id(source_filename)
    job_dir = JOBS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "digital").mkdir(exist_ok=True)
    (job_dir / "scans").mkdir(exist_ok=True)
    (job_dir / "decoded").mkdir(exist_ok=True)
    metadata = {
        "job_id": job_id,
        "source_file": source_filename,
        "profile": profile_name,
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


def scans_page_dir(job_dir: Path, page_index: int) -> Path:
    d = job_dir / "scans" / f"page_{page_index + 1:03d}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def decoded_dir(job_dir: Path) -> Path:
    d = job_dir / "decoded"
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_job_metadata(job_dir: Path) -> dict:
    meta_path = job_dir / "job.json"
    if not meta_path.exists():
        return {}
    return json.loads(meta_path.read_text())


def update_job_metadata(job_dir: Path, updates: dict) -> None:
    meta = load_job_metadata(job_dir)
    meta.update(updates)
    (job_dir / "job.json").write_text(json.dumps(meta, indent=2))


def list_jobs() -> list[tuple[str, Path, dict]]:
    if not JOBS_DIR.exists():
        return []
    results = []
    for d in sorted(JOBS_DIR.iterdir()):
        if d.is_dir() and (d / "job.json").exists():
            meta = load_job_metadata(d)
            results.append((d.name, d, meta))
    return results


def find_job(job_id_prefix: str) -> Path | None:
    if not JOBS_DIR.exists():
        return None
    for d in JOBS_DIR.iterdir():
        if d.is_dir() and d.name.startswith(job_id_prefix):
            return d
    return None


def models_dir(profile_name: str) -> Path:
    d = MODELS_DIR / "cell_classifier" / profile_name
    d.mkdir(parents=True, exist_ok=True)
    return d


def checkpoints_dir(profile_name: str) -> Path:
    d = MODELS_DIR / "cell_classifier" / profile_name / "checkpoints"
    d.mkdir(parents=True, exist_ok=True)
    return d


def training_pairs_dir(profile_name: str) -> Path:
    d = TRAINING_DIR / "pairs" / profile_name
    d.mkdir(parents=True, exist_ok=True)
    return d
