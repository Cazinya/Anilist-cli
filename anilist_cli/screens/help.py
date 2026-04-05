"""Help modal screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Button, Static


HELP_TEXT = """\
[bold cyan]AniList CLI — Keyboard Shortcuts[/bold cyan]

[bold]Navigation[/bold]
  [bold]1[/bold]           Go to Home (Trending)
  [bold]2[/bold]           Go to Search
  [bold]3[/bold]           Go to My List
  [bold]4[/bold]           Go to Profile
  [bold]q[/bold]           Quit / go back
  [bold]Escape[/bold]      Go back / close modal

[bold]Movement[/bold]
  [bold]j / ↓[/bold]       Move down
  [bold]k / ↑[/bold]       Move up
  [bold]Tab[/bold]         Switch tabs

[bold]Search[/bold]
  [bold]/[/bold]           Focus search input
  [bold]Enter[/bold]       Submit search / select item
  [bold]Escape[/bold]      Clear search

[bold]My List[/bold]
  [bold]Enter[/bold]       Open media details
  [bold]e[/bold]           Edit list entry
  [bold]r[/bold]           Refresh list

[bold]Media Details[/bold]
  [bold]a / e[/bold]       Add to / Edit list entry
  [bold]Escape[/bold]      Go back

[bold]General[/bold]
  [bold]r[/bold]           Refresh current view
  [bold]?[/bold]           Show this help
"""


class HelpScreen(ModalScreen):
    """Displays keyboard shortcuts and help information."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("q", "dismiss", "Close"),
        Binding("?", "dismiss", "Close"),
    ]

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }
    HelpScreen #help-box {
        width: 60;
        height: auto;
        max-height: 40;
        border: double $accent;
        background: $surface;
        padding: 2 4;
        layout: vertical;
        overflow-y: auto;
    }
    HelpScreen #close-btn {
        width: 100%;
        margin-top: 2;
    }
    """

    def compose(self) -> ComposeResult:
        with Static(id="help-box"):
            yield Static(HELP_TEXT)
            yield Button("Close [Escape]", variant="default", id="close-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-btn":
            self.dismiss()
