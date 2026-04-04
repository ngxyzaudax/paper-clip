import importlib

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from cli.tui.encode_screen import EncodeScreen
from cli.tui.nav_config import (
    DEFAULT_NAV_ID,
    NAV_FULL,
    NAV_GROUPS,
    NAV_SHORT,
    PANEL_REGISTRY,
    status_text,
)


class MainScreen(Screen):
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("backslash", "toggle_sidebar", "Sidebar"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._collapsed: bool = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="app-layout"):
            with Vertical(id="sidebar"):
                yield Static("PAPER·CLIP", id="sidebar-brand")
                with VerticalScroll(id="sidebar-nav"):
                    for group_label, items in NAV_GROUPS:
                        yield Static(group_label, classes="nav-group")
                        for btn_id, label, _ in items:
                            yield Button(label, id=btn_id, classes="nav-btn", compact=True)
                yield Static("", id="sidebar-status")
                yield Button("◀ Collapse", id="sidebar-toggle", compact=True)
                yield Button("Quit", id="nav-quit", variant="error", compact=True)
            with Vertical(id="content-area"):
                yield EncodeScreen()
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#sidebar-status", Static).update(status_text())
        self.query_one(f"#{DEFAULT_NAV_ID}", Button).add_class("-active")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "nav-quit":
            self.app.exit()
        elif btn_id == "sidebar-toggle":
            self.action_toggle_sidebar()
        elif btn_id in PANEL_REGISTRY:
            self._switch_panel(btn_id)

    def _switch_panel(self, nav_id: str) -> None:
        for btn in self.query(".nav-btn"):
            btn.remove_class("-active")
        self.query_one(f"#{nav_id}", Button).add_class("-active")
        content = self.query_one("#content-area")
        content.remove_children()
        mod_path, cls_name = PANEL_REGISTRY[nav_id]
        panel_cls = getattr(importlib.import_module(mod_path), cls_name)
        content.mount(panel_cls())

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one("#sidebar")
        toggle = self.query_one("#sidebar-toggle", Button)
        self._collapsed = not self._collapsed
        if self._collapsed:
            sidebar.add_class("collapsed")
            toggle.label = "▶"
            self.query_one("#sidebar-brand", Static).update("PC")
            for g in self.query(".nav-group"):
                g.display = False
            self.query_one("#sidebar-status", Static).display = False
            self.query_one("#nav-quit", Button).label = "X"
            for nav_id, short in NAV_SHORT.items():
                self.query_one(f"#{nav_id}", Button).label = short
        else:
            sidebar.remove_class("collapsed")
            toggle.label = "◀ Collapse"
            self.query_one("#sidebar-brand", Static).update("PAPER·CLIP")
            for g in self.query(".nav-group"):
                g.display = True
            self.query_one("#sidebar-status", Static).display = True
            self.query_one("#nav-quit", Button).label = "Quit"
            for nav_id, full in NAV_FULL.items():
                self.query_one(f"#{nav_id}", Button).label = full

    def action_quit(self) -> None:
        self.app.exit()


class PaperClipApp(App):
    CSS_PATH = "styles.tcss"
    TITLE = "Paper-Clip"
    SUB_TITLE = "Data serialization to physical paper"

    def on_mount(self) -> None:
        self.push_screen(MainScreen())


def run_tui() -> None:
    PaperClipApp().run()
