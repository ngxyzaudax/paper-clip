from common.log_config import setup_logging


def main() -> None:
    setup_logging(console=True)
    from cli.app import app
    app()


if __name__ == "__main__":
    main()
