import sys

from common.log_config import setup_logging


def main() -> None:
    is_tui = len(sys.argv) == 1
    setup_logging(console=not is_tui)

    from cli.app import app
    app()


if __name__ == "__main__":
    main()
