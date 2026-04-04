from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Button, Input, Label, ProgressBar, Select, Static

from common.config_store import list_profiles


class MLScreen(Widget):

    def __init__(self) -> None:
        super().__init__()
        self._extract_job_snap: str = ""
        self._train_profile_snap: str = ""
        self._train_epochs_snap: int = 30
        self._train_batch_snap: int = 128
        self._train_cell_snap: str = ""

    def compose(self) -> ComposeResult:
        prof_opts = [(n, n) for n, _ in list_profiles()]
        with VerticalScroll(classes="form-container"):
            yield Static("Machine learning", classes="screen-title")
            with Vertical(classes="section"):
                yield Static("Extract training data", classes="section-title")
                yield Label("Job ID prefix")
                yield Input(placeholder="capture job to extract cells from", id="extract-job-input")
                yield Button("Extract to TFRecord", id="btn-extract", variant="primary")
            with Vertical(classes="section"):
                yield Static("Train classifier", classes="section-title")
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-col"):
                        yield Label("Profile")
                        yield Select(prof_opts, prompt="Select profile", id="train-profile-select")
                    with Vertical(classes="form-col"):
                        yield Label("Epochs")
                        yield Input(value="30", id="epochs-input")
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-col"):
                        yield Label("Batch size")
                        yield Input(value="128", id="batch-input")
                    with Vertical(classes="form-col"):
                        yield Label("Cell size px (optional)")
                        yield Input(placeholder="auto from profile", id="cell-input")
                yield Button("Train", id="btn-train", variant="primary")
            yield ProgressBar(id="progress")
            yield Static("", id="status")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-extract":
            self._extract_job_snap = self.query_one("#extract-job-input", Input).value.strip()
            self.query_one("#btn-extract", Button).disabled = True
            self._run_extract()
        elif event.button.id == "btn-train":
            pv = self.query_one("#train-profile-select", Select).value
            if pv == Select.BLANK:
                self.query_one("#status", Static).update("[yellow]Select a profile[/yellow]")
                return
            self._train_profile_snap = str(pv)
            self._train_epochs_snap = int(self.query_one("#epochs-input", Input).value or "30")
            self._train_batch_snap = int(self.query_one("#batch-input", Input).value or "128")
            c = self.query_one("#cell-input", Input).value.strip()
            self._train_cell_snap = c
            self.query_one("#btn-train", Button).disabled = True
            self._run_train()

    @work(thread=True)
    def _run_extract(self) -> None:
        try:
            from cli.training_cmd import extract_training_data
            if not self._extract_job_snap:
                raise ValueError("Enter a job ID prefix")
            out, n, summary = extract_training_data(self._extract_job_snap)
            msg = f"[bold green]Wrote {n:,} examples[/bold green]\n{out}\n\n{summary}"
        except ValueError as e:
            msg = f"[bold red]{e}[/bold red]"
        except Exception as e:
            msg = f"[bold red]Error: {e}[/bold red]"
        self.app.call_from_thread(self._extract_done, msg)

    def _extract_done(self, msg: str) -> None:
        self.query_one("#progress", ProgressBar).update(total=100, progress=100)
        self.query_one("#status", Static).update(msg)
        self.query_one("#btn-extract", Button).disabled = False

    @work(thread=True)
    def _run_train(self) -> None:
        try:
            from cli.train_cmd import run_classifier_training
            cell_opt = int(self._train_cell_snap) if self._train_cell_snap else None
            acc, mdir = run_classifier_training(
                self._train_profile_snap,
                self._train_epochs_snap,
                self._train_batch_snap,
                cell_opt,
            )
            msg = f"[bold green]Validation accuracy: {acc:.2%}[/bold green]\nModel: {mdir}/"
        except ValueError as e:
            msg = f"[bold red]{e}[/bold red]"
        except Exception as e:
            msg = f"[bold red]Error: {e}[/bold red]"
        self.app.call_from_thread(self._train_done, msg)

    def _train_done(self, msg: str) -> None:
        self.query_one("#progress", ProgressBar).update(total=100, progress=100)
        self.query_one("#status", Static).update(msg)
        self.query_one("#btn-train", Button).disabled = False
