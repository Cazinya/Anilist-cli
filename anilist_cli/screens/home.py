"""Home screen — trending anime and manga."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import (
    Footer,
    Header,
    Label,
    LoadingIndicator,
    TabbedContent,
    TabPane,
)
from textual.containers import ScrollableContainer, Horizontal

from ..models.media import Media
from ..widgets.media_card import MediaCard


class MediaGrid(ScrollableContainer):
    """Scrollable horizontal-wrapping grid of MediaCard widgets."""

    DEFAULT_CSS = """
    MediaGrid {
        layout: grid;
        grid-size: 5;
        grid-gutter: 1;
        padding: 1;
        width: 100%;
        height: 1fr;
        overflow-y: auto;
    }
    """


class HomeScreen(Screen):
    """Displays trending anime and manga in a tabbed grid layout."""

    BINDINGS = [
        Binding("r", "refresh", "Refresh"),
        Binding("2", "app.switch_mode('search')", "Search", show=False),
        Binding("3", "app.switch_mode('my_list')", "My List", show=False),
        Binding("4", "app.switch_mode('profile')", "Profile", show=False),
        Binding("q", "app.quit", "Quit"),
        Binding("?", "show_help", "Help"),
    ]

    DEFAULT_CSS = """
    HomeScreen {
        layout: vertical;
    }
    HomeScreen TabbedContent {
        height: 1fr;
    }
    HomeScreen LoadingIndicator {
        height: 1fr;
    }
    HomeScreen .empty-msg {
        text-align: center;
        color: $text-muted;
        padding: 4;
    }
    HomeScreen TabPane {
        padding: 0;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent(id="home-tabs"):
            with TabPane("Trending Anime", id="tab-trending-anime"):
                yield LoadingIndicator(id="loading-anime")
            with TabPane("Trending Manga", id="tab-trending-manga"):
                yield LoadingIndicator(id="loading-manga")
            with TabPane("Popular Anime", id="tab-popular-anime"):
                yield LoadingIndicator(id="loading-popular-anime")
            with TabPane("Popular Manga", id="tab-popular-manga"):
                yield LoadingIndicator(id="loading-popular-manga")
        yield Footer()

    def on_mount(self) -> None:
        self.run_worker(self._load_trending_anime(), name="trending_anime", exclusive=False)
        self.run_worker(self._load_trending_manga(), name="trending_manga", exclusive=False)

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        tab_id = event.tab.id if event.tab else None
        if tab_id == "tab--tab-popular-anime":
            pane = self.query_one("#tab-popular-anime", TabPane)
            if not pane.query(MediaGrid):
                self.run_worker(self._load_popular_anime(), name="popular_anime", exclusive=False)
        elif tab_id == "tab--tab-popular-manga":
            pane = self.query_one("#tab-popular-manga", TabPane)
            if not pane.query(MediaGrid):
                self.run_worker(self._load_popular_manga(), name="popular_manga", exclusive=False)

    async def _load_trending_anime(self) -> None:
        try:
            media_list = await self.app.api_client.get_trending("ANIME", per_page=20)
            loading = self.query_one("#loading-anime", LoadingIndicator)
            await loading.remove()
            pane = self.query_one("#tab-trending-anime", TabPane)
            grid = MediaGrid(id="grid-trending-anime")
            await pane.mount(grid)
            for media in media_list:
                await grid.mount(
                    MediaCard(media, show_images=self.app.config.show_images)
                )
        except Exception as e:
            self._show_error("#tab-trending-anime", "#loading-anime", str(e))

    async def _load_trending_manga(self) -> None:
        try:
            media_list = await self.app.api_client.get_trending("MANGA", per_page=20)
            loading = self.query_one("#loading-manga", LoadingIndicator)
            await loading.remove()
            pane = self.query_one("#tab-trending-manga", TabPane)
            grid = MediaGrid(id="grid-trending-manga")
            await pane.mount(grid)
            for media in media_list:
                await grid.mount(
                    MediaCard(media, show_images=self.app.config.show_images)
                )
        except Exception as e:
            self._show_error("#tab-trending-manga", "#loading-manga", str(e))

    async def _load_popular_anime(self) -> None:
        try:
            media_list = await self.app.api_client.get_popular("ANIME", per_page=20)
            try:
                loading = self.query_one("#loading-popular-anime", LoadingIndicator)
                await loading.remove()
            except Exception:
                pass
            pane = self.query_one("#tab-popular-anime", TabPane)
            grid = MediaGrid(id="grid-popular-anime")
            await pane.mount(grid)
            for media in media_list:
                await grid.mount(
                    MediaCard(media, show_images=self.app.config.show_images)
                )
        except Exception as e:
            self._show_error("#tab-popular-anime", "#loading-popular-anime", str(e))

    async def _load_popular_manga(self) -> None:
        try:
            media_list = await self.app.api_client.get_popular("MANGA", per_page=20)
            try:
                loading = self.query_one("#loading-popular-manga", LoadingIndicator)
                await loading.remove()
            except Exception:
                pass
            pane = self.query_one("#tab-popular-manga", TabPane)
            grid = MediaGrid(id="grid-popular-manga")
            await pane.mount(grid)
            for media in media_list:
                await grid.mount(
                    MediaCard(media, show_images=self.app.config.show_images)
                )
        except Exception as e:
            self._show_error("#tab-popular-manga", "#loading-popular-manga", str(e))

    def _show_error(self, pane_id: str, loading_id: str, msg: str) -> None:
        try:
            loading = self.query_one(loading_id, LoadingIndicator)
            loading.remove()
        except Exception:
            pass
        try:
            pane = self.query_one(pane_id, TabPane)
            pane.mount(Label(f"[red]Error loading data: {msg}[/red]", classes="empty-msg"))
        except Exception:
            pass

    def on_media_card_selected(self, event: MediaCard.Selected) -> None:
        from .details import MediaDetailsScreen
        self.app.push_screen(MediaDetailsScreen(event.media.id))

    def action_refresh(self) -> None:
        self.app.switch_mode("home")

    def action_show_help(self) -> None:
        from .help import HelpScreen
        self.app.push_screen(HelpScreen())
