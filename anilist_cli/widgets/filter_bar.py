"""Filter bar widget for search screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Select, Label

ANIME_GENRES = [
    "Action", "Adventure", "Comedy", "Drama", "Ecchi", "Fantasy",
    "Horror", "Mahou Shoujo", "Mecha", "Music", "Mystery", "Psychological",
    "Romance", "Sci-Fi", "Slice of Life", "Sports", "Supernatural", "Thriller",
]

MANGA_GENRES = ANIME_GENRES + ["Hentai"]

MEDIA_STATUSES = [
    ("Any Status", None),
    ("Finished", "FINISHED"),
    ("Currently Airing/Publishing", "RELEASING"),
    ("Not Yet Released", "NOT_YET_RELEASED"),
    ("Cancelled", "CANCELLED"),
    ("Hiatus", "HIATUS"),
]

ANIME_FORMATS = [
    ("Any Format", None),
    ("TV", "TV"),
    ("TV Short", "TV_SHORT"),
    ("Movie", "MOVIE"),
    ("Special", "SPECIAL"),
    ("OVA", "OVA"),
    ("ONA", "ONA"),
    ("Music", "MUSIC"),
]

MANGA_FORMATS = [
    ("Any Format", None),
    ("Manga", "MANGA"),
    ("Novel", "NOVEL"),
    ("One Shot", "ONE_SHOT"),
]

SORT_OPTIONS = [
    ("Popularity", "POPULARITY_DESC"),
    ("Score", "SCORE_DESC"),
    ("Trending", "TRENDING_DESC"),
    ("Newest", "START_DATE_DESC"),
    ("Oldest", "START_DATE"),
    ("Title A-Z", "TITLE_ROMAJI"),
    ("Favourites", "FAVOURITES_DESC"),
]

SEASONS = [
    ("Any Season", None),
    ("Winter", "WINTER"),
    ("Spring", "SPRING"),
    ("Summer", "SUMMER"),
    ("Fall", "FALL"),
]

import datetime
CURRENT_YEAR = datetime.date.today().year
YEAR_OPTIONS = [("Any Year", None)] + [(str(y), y) for y in range(CURRENT_YEAR + 1, 1989, -1)]


class FilterBar(Widget):
    """Horizontal bar of filter dropdowns for searching media."""

    DEFAULT_CSS = """
    FilterBar {
        layout: horizontal;
        height: 3;
        width: 100%;
        background: $panel;
        padding: 0 1;
    }
    FilterBar Label {
        height: 3;
        content-align: center middle;
        padding: 0 1;
        color: $text-muted;
    }
    FilterBar Select {
        width: 18;
        margin: 0 1;
    }
    """

    class Changed(Message):
        def __init__(self, filters: dict) -> None:
            super().__init__()
            self.filters = filters

    def __init__(self, media_type: str = "ANIME", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._media_type = media_type

    def compose(self) -> ComposeResult:
        genres = [(f"Genre: Any", None)] + [(g, g) for g in ANIME_GENRES]
        formats = ANIME_FORMATS if self._media_type == "ANIME" else MANGA_FORMATS

        yield Label("Sort:")
        yield Select(
            [(label, val) for label, val in SORT_OPTIONS],
            value="POPULARITY_DESC",
            id="sort-select",
        )
        yield Label("Genre:")
        yield Select(
            genres,
            value=None,
            allow_blank=True,
            id="genre-select",
        )
        yield Label("Status:")
        yield Select(
            [(label, val) for label, val in MEDIA_STATUSES],
            value=None,
            allow_blank=True,
            id="status-select",
        )
        yield Label("Format:")
        yield Select(
            [(label, val) for label, val in formats],
            value=None,
            allow_blank=True,
            id="format-select",
        )
        if self._media_type == "ANIME":
            yield Label("Season:")
            yield Select(
                [(label, val) for label, val in SEASONS],
                value=None,
                allow_blank=True,
                id="season-select",
            )
        yield Label("Year:")
        yield Select(
            YEAR_OPTIONS,
            value=None,
            allow_blank=True,
            id="year-select",
        )

    def get_filters(self) -> dict:
        def val(widget_id: str):
            try:
                w = self.query_one(f"#{widget_id}", Select)
                v = w.value
                return v if v != Select.BLANK else None
            except Exception:
                return None

        return {
            "sort": val("sort-select"),
            "genre": val("genre-select"),
            "status": val("status-select"),
            "format": val("format-select"),
            "season": val("season-select"),
            "season_year": val("year-select"),
        }

    def on_select_changed(self) -> None:
        self.post_message(self.Changed(self.get_filters()))
