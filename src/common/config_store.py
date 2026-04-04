from pathlib import Path

from common.config import PaperClipConfig, load_config, save_config
from common.data_store import DATA_ROOT

CONFIGS_DIR = DATA_ROOT / "configs"


def ensure_configs_dir() -> Path:
    CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIGS_DIR


def list_profiles() -> list[tuple[str, Path]]:
    ensure_configs_dir()
    return [
        (p.stem, p)
        for p in sorted(CONFIGS_DIR.iterdir())
        if p.suffix == ".toml" and p.is_file()
    ]


def load_profile(name: str) -> PaperClipConfig:
    path = CONFIGS_DIR / f"{name}.toml"
    if not path.exists():
        raise FileNotFoundError(f"Config profile not found: {name}")
    return load_config(path)


def save_profile(name: str, config: PaperClipConfig) -> Path:
    ensure_configs_dir()
    path = CONFIGS_DIR / f"{name}.toml"
    save_config(config, path)
    return path


def profile_exists(name: str) -> bool:
    return (CONFIGS_DIR / f"{name}.toml").exists()


def detect_profile_name(config: PaperClipConfig) -> str | None:
    for name, _ in list_profiles():
        try:
            p = load_profile(name)
            if (p.num_colors == config.num_colors
                    and p.cell_size_px == config.cell_size_px
                    and abs(p.rs_redundancy - config.rs_redundancy) < 1e-6
                    and p.calibrated_colors == config.calibrated_colors):
                return name
        except Exception:
            continue
    return None
