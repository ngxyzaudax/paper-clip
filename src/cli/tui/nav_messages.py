from textual.message import Message


class OpenPanel(Message):
    """Ask the main screen to switch panels, optionally preselecting a job in the new panel."""

    def __init__(self, nav_id: str, job_id: str | None = None) -> None:
        super().__init__()
        self.nav_id = nav_id
        self.job_id = job_id
