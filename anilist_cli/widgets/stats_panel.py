"""Stats panel widget for the profile screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from ..models.user import UserStats


def _bar(value: int, max_value: int, width: int = 20, filled: str = "█", empty: str = "░") -> str:
    if max_value == 0:
        return empty * width
    filled_count = round(value / max_value * width)
    return filled * filled_count + empty * (width - filled_count)


class StatsPanel(Widget):
    """Renders anime/manga statistics with bar charts."""

    DEFAULT_CSS = """
    StatsPanel {
        layout: vertical;
        padding: 1 2;
        background: $surface;
        border: tall $panel-lighten-1;
        margin: 1;
    }
    StatsPanel .stats-header {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    StatsPanel .stats-row {
        color: $text;
        margin: 0;
    }
    StatsPanel .stats-bar {
        color: $accent;
    }
    StatsPanel .genre-bar-anime {
        color: cyan;
    }
    StatsPanel .genre-bar-manga {
        color: magenta;
    }
    """

    def __init__(self, stats: UserStats, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stats = stats

    def compose(self) -> ComposeResult:
        s = self._stats

        # ---- Anime section ----
        yield Static("[bold cyan]Anime Statistics[/bold cyan]", classes="stats-header")
        yield Static(f"Total: [bold]{s.anime_count}[/bold]   "
                     f"Mean Score: [bold]{s.anime_mean_score:.1f}[/bold]   "
                     f"Days Watched: [bold]{s.anime_days_watched}[/bold]   "
                     f"Episodes: [bold]{s.anime_episodes_watched:,}[/bold]", classes="stats-row")

        yield Static("")
        yield Static("[dim]Status Breakdown:[/dim]", classes="stats-row")
        total_anime = s.anime_count or 1
        for label, count in [
            ("Watching  ", s.anime_watching),
            ("Completed ", s.anime_completed),
            ("On Hold   ", s.anime_paused),
            ("Dropped   ", s.anime_dropped),
            ("Planning  ", s.anime_planning),
        ]:
            bar = _bar(count, total_anime, 25)
            yield Static(f"  {label} [cyan]{bar}[/cyan] {count}", classes="stats-row")

        # Top genres
        if s.top_anime_genres:
            yield Static("")
            yield Static("[dim]Top Genres (Anime):[/dim]", classes="stats-row")
            max_count = max(g.count for g in s.top_anime_genres)
            for g in s.top_anime_genres[:8]:
                bar = _bar(g.count, max_count, 20)
                genre_name = g.genre[:16].ljust(16)
                yield Static(
                    f"  {genre_name} [cyan]{bar}[/cyan] {g.count} (avg {g.mean_score:.0f})",
                    classes="stats-row"
                )

        yield Static("")
        yield Static("─" * 60, classes="stats-row")
        yield Static("")

        # ---- Manga section ----
        yield Static("[bold magenta]Manga Statistics[/bold magenta]", classes="stats-header")
        yield Static(f"Total: [bold]{s.manga_count}[/bold]   "
                     f"Mean Score: [bold]{s.manga_mean_score:.1f}[/bold]   "
                     f"Chapters: [bold]{s.manga_chapters_read:,}[/bold]   "
                     f"Volumes: [bold]{s.manga_volumes_read:,}[/bold]", classes="stats-row")

        yield Static("")
        yield Static("[dim]Status Breakdown:[/dim]", classes="stats-row")
        total_manga = s.manga_count or 1
        for label, count in [
            ("Reading   ", s.manga_reading),
            ("Completed ", s.manga_completed),
            ("On Hold   ", s.manga_paused),
            ("Dropped   ", s.manga_dropped),
            ("Planning  ", s.manga_planning),
        ]:
            bar = _bar(count, total_manga, 25)
            yield Static(f"  {label} [magenta]{bar}[/magenta] {count}", classes="stats-row")

        if s.top_manga_genres:
            yield Static("")
            yield Static("[dim]Top Genres (Manga):[/dim]", classes="stats-row")
            max_count = max(g.count for g in s.top_manga_genres)
            for g in s.top_manga_genres[:8]:
                bar = _bar(g.count, max_count, 20)
                genre_name = g.genre[:16].ljust(16)
                yield Static(
                    f"  {genre_name} [magenta]{bar}[/magenta] {g.count} (avg {g.mean_score:.0f})",
                    classes="stats-row"
                )
