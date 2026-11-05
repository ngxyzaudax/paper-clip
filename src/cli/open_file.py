import subprocess
import sys
from pathlib import Path


def open_with_system(path: Path) -> bool:
    """Show a file in the desktop's default viewer; False when no viewer could be started."""
    command = "open" if sys.platform == "darwin" else "xdg-open"
    try:
        subprocess.Popen([command, str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        return False
    return True
