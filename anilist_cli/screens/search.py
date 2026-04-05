"""Search screen — search anime and manga with filters."""

from __future__ import annotations

import asyncio

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    LoadingIndicator,
    Select,
    Static,
    TabbedContent,
    TabPane,
)

from ..models.media import Media
from ..widgets.filter_bar import FilterBar
from ..widgets.media_card import MediaCard


class SearchResultsGrid(ScrollableContainer):
    DEFAULT_CSS = """
    SearchResultsGrid {
        layout: grid;
        grid-size: 5;
        grid-gutter: 1;
        padding: 1;
        width: 100%;
        height: 1fr;
        overflow-y: auto;
    }
    """


class SearchScreen(Screen):
    """Full-featured search screen with filters for anime and manga."""

    BINDINGS = [
        Binding("/", "focus_search", "Search", show=True),
        Binding("1", "app.switch_mode('home')", "Home", show=False),
        Binding("3", "app.switch_mode('my_list')", "My List", show=False),
        Binding("4", "app.switch_mode('profile')", "Profile", show=False),
        Binding("q", "app.quit", "Quit"),
        Binding("escape", "clear_search", "Clear"),
    ]

    DEFAULT_CSS = """
    SearchScreen {
        layout: vertical;
    }
    SearchScreen #search-bar {
        layout: horizontal;
        height: 3;
        padding: 0 1;
        background: $panel;
    }
    SearchScreen #search-input {
        width: 1fr;
        margin: 0 1;
    }
    SearchScreen #type-toggle {
        width: 16;
    }
    SearchScreen #search-btn {
        width: 12;
    }
    SearchScreen FilterBar {
        height: 3;
    }
    SearchScreen TabbedContent {
        height: 1fr;
    }
    SearchScreen .status-bar {
        height: 1;
        background: $panel-darken-1;
        color: $text-muted;
        padding: 0 2;
        content-align: left middle;
    }
    SearchScreen .empty-hint {
        text-align: center;
        color: $text-muted;
        padding: 4;
        height: 1fr;
        content-align: center middle;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_type = "ANIME"
        self._search_task: asyncio.Task | None = None
        self._debounce_task: asyncio.Task | None = None
        self._current_page = 1
        self._has_next_page = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Static(id="search-bar"):
            yield Select(
                [("Anime", "ANIME"), ("Manga", "MANGA")],
                value="ANIME",
                id="type-toggle",
            )
            yield Input(
                placeholder="Search anime or manga…",
                id="search-input",
            )
            yield Button("Search", variant="primary", id="search-btn")
        yield FilterBar(media_type="ANIME", id="filter-bar")
        yield Static("Type a title to search, or browse with filters.", classes="empty-hint", id="status-bar")
        yield SearchResultsGrid(id="results-grid")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#search-input", Input).focus()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "type-toggle":
            self._current_type = str(event.value)
            # Rebuild filter bar for correct format options
            try:
                old_bar = self.query_one("#filter-bar", FilterBar)
                new_bar = FilterBar(media_type=self._current_type, id="filter-bar")
                old_bar.replace_with(new_bar)
            except Exception:
                pass
            self._trigger_search()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search-input":
            self._schedule_debounced_search()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "search-input":
            self._trigger_search()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "search-btn":
            self._trigger_search()

    def on_filter_bar_changed(self, event: FilterBar.Changed) -> None:
        self._trigger_search()

    def _schedule_debounced_search(self) -> None:
        if self._debounce_task and self._debounce_task.is_running:
            self._debounce_task.cancel()
        self._debounce_task = self.run_worker(
            self._debounce_search(), name="debounce", exclusive=False
        )

    async def _debounce_search(self) -> None:
        await asyncio.sleep(0.4)
        self._trigger_search()

    def _trigger_search(self) -> None:
        self._current_page = 1
        self.run_worker(self._do_search(), name="search", exclusive=True)

    async def _do_search(self) -> None:
        search_input = self.query_one("#search-input", Input)
        query = search_input.value.strip() or None

        try:
            filter_bar = self.query_one("#filter-bar", FilterBar)
            filters = filter_bar.get_filters()
        except Exception:
            filters = {}

        status_bar = self.query_one("#status-bar", Static)
        results_grid = self.query_one("#results-grid", SearchResultsGrid)

        status_bar.update("Searching…")
        await results_grid.remove_children()

        if not query and not any(v for v in filters.values()):
            status_bar.update("Type a title to search, or browse with filters.")
            return

        try:
            media_list, has_next = await self.app.api_client.search_media(
                search=query,
                media_type=self._current_type,
                genre=filters.get("genre"),
                status=filters.get("status"),
                format=filters.get("format"),
                sort=[filters["sort"]] if filters.get("sort") else None,
                season=filters.get("season"),
                season_year=filters.get("season_year"),
                page=self._current_page,
                per_page=20,
            )
            self._has_next_page = has_next

            if not media_list:
                status_bar.update("No results found.")
                return

            count_str = f"{len(media_list)} results" + (" (more available)" if has_next else "")
            status_bar.update(count_str)

            for media in media_list:
                await results_grid.mount(
                    MediaCard(media, show_images=self.app.config.show_images)
                )
        except Exception as e:
            status_bar.update(f"[red]Error: {e}[/red]")

    def on_media_card_selected(self, event: MediaCard.Selected) -> None:
        from .details import MediaDetailsScreen
        self.app.push_screen(MediaDetailsScreen(event.media.id))

    def action_focus_search(self) -> None:
        self.query_one("#search-input", Input).focus()

    def action_clear_search(self) -> None:
        search_input = self.query_one("#search-input", Input)
        search_input.clear()
        try:
            results_grid = self.query_one("#results-grid", SearchResultsGrid)
            self.run_worker(results_grid.remove_children(), exclusive=False)
        except Exception:
            pass
        status_bar = self.query_one("#status-bar", Static)
        status_bar.update("Type a title to search, or browse with filters.")
