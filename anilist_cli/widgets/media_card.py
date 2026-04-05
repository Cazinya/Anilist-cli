"""Media card widget for displaying anime/manga in a grid."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, Static

from ..models.media import Media
from .cover_image import CoverImage


class MediaCard(Widget):
    """
    A compact card showing a media's cover, title, score, format, and type.
    Emits a `Selected` message when activated.
    """

    DEFAULT_CSS = """
    MediaCard {
        width: 24;
        height: 20;
        border: tall $panel-lighten-1;
        background: $surface;
        margin: 1;
        padding: 0;
        layout: vertical;
    }
    MediaCard:hover {
        border: tall $accent;
    }
    MediaCard:focus {
        border: tall $accent;
        background: $boost;
    }
    MediaCard .card-image {
        height: 13;
        width: 100%;
        content-align: center top;
    }
    MediaCard .card-info {
        height: 7;
        width: 100%;
        padding: 0 1;
    }
    MediaCard .card-title {
        text-overflow: ellipsis;
        width: 100%;
        color: $text;
        text-style: bold;
    }
    MediaCard .card-meta {
        color: $text-muted;
        width: 100%;
    }
    MediaCard .card-score-green {
        color: $success;
        text-style: bold;
    }
    MediaCard .card-score-yellow {
        color: $warning;
        text-style: bold;
    }
    MediaCard .card-score-red {
        color: $error;
        text-style: bold;
    }
    MediaCard .card-score-none {
        color: $text-muted;
    }
    """

    BINDINGS = [
        ("enter", "select", "Select"),
    ]

    class Selected(Message):
        def __init__(self, media: Media) -> None:
            super().__init__()
            self.media = media

    def __init__(self, media: Media, show_images: bool = True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.media = media
        self._show_images = show_images
        self.can_focus = True

    def compose(self) -> ComposeResult:
        with Static(classes="card-image"):
            yield CoverImage(
                url=self.media.cover_url,
                title=self.media.display_title,
                width=22,
                height=13,
                show_images=self._show_images,
            )
        with Static(classes="card-info"):
            title = self.media.display_title
            yield Label(title[:20] + ("…" if len(title) > 20 else ""), classes="card-title")
            score_str, score_class = self._score_display()
            format_str = self.media.format or self.media.type
            year = f" · {self.media.season_year or self.media.year}" if (self.media.season_year or self.media.year) else ""
            yield Label(f"{format_str}{year}", classes="card-meta")
            yield Label(f"★ {score_str}", classes=score_class)

    def _score_display(self) -> tuple[str, str]:
        score = self.media.score
        if score is None:
            return "N/A", "card-score-none"
        val = score / 10
        if val >= 7.5:
            return f"{val:.1f}", "card-score-green"
        if val >= 5.0:
            return f"{val:.1f}", "card-score-yellow"
        return f"{val:.1f}", "card-score-red"

    def action_select(self) -> None:
        self.post_message(self.Selected(self.media))

    def on_click(self) -> None:
        self.action_select()
