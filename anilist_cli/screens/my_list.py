"""My list screen — user's anime and manga lists."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Label,
    LoadingIndicator,
    Select,
    Static,
    TabbedContent,
    TabPane,
)

from ..models.media import MediaList, MediaListGroup
from ..widgets.cover_image import CoverImage


STATUS_TAB_ORDER = [
    ("CURRENT", "Watching/Reading"),
    ("REPEATING", "Rewatching/Rereading"),
    ("COMPLETED", "Completed"),
    ("PAUSED", "On Hold"),
    ("DROPPED", "Dropped"),
    ("PLANNING", "Plan to Watch/Read"),
]


class MyListScreen(Screen):
    """Displays and manages the user's anime and manga lists."""

    BINDINGS = [
        Binding("1", "app.switch_mode('home')", "Home", show=False),
        Binding("2", "app.switch_mode('search')", "Search", show=False),
        Binding("4", "app.switch_mode('profile')", "Profile", show=False),
        Binding("q", "app.quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("e", "edit_selected", "Edit"),
        Binding("enter", "open_details", "Details"),
    ]

    DEFAULT_CSS = """
    MyListScreen {
        layout: vertical;
    }
    MyListScreen #type-bar {
        layout: horizontal;
        height: 3;
        background: $panel;
        padding: 0 2;
        align-vertical: middle;
    }
    MyListScreen #type-bar Label {
        content-align: center middle;
        margin-right: 1;
        color: $text-muted;
    }
    MyListScreen #type-bar Button {
        margin-right: 1;
    }
    MyListScreen TabbedContent {
        height: 1fr;
    }
    MyListScreen DataTable {
        height: 1fr;
    }
    MyListScreen .empty-msg {
        color: $text-muted;
        text-align: center;
        padding: 4;
    }
    MyListScreen #loading-list {
        height: 1fr;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_type = "ANIME"
        self._groups: list[MediaListGroup] = []
        # Map: (status, row_key) -> MediaList entry
        self._entry_map: dict[str, dict[str, MediaList]] = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Static(id="type-bar"):
            yield Label("Type:")
            yield Button("Anime", variant="primary", id="btn-anime")
            yield Button("Manga", variant="default", id="btn-manga")
        yield LoadingIndicator(id="loading-list")
        yield Footer()

    def on_mount(self) -> None:
        self.run_worker(self._load_lists(), name="load_lists", exclusive=True)

    async def _load_lists(self) -> None:
        if not self.app.current_user:
            return
        try:
            groups = await self.app.api_client.get_media_list(
                self.app.current_user.id,
                self._current_type,
            )
            self._groups = groups

            try:
                loading = self.query_one("#loading-list", LoadingIndicator)
                await loading.remove()
            except Exception:
                pass

            # Remove existing tabs if any
            try:
                old_tabs = self.query_one("#list-tabs", TabbedContent)
                await old_tabs.remove()
            except Exception:
                pass

            await self._build_tabs(groups)
        except Exception as e:
            try:
                loading = self.query_one("#loading-list", LoadingIndicator)
                await loading.remove()
            except Exception:
                pass
            await self.mount(Label(f"[red]Failed to load lists: {e}[/red]"))

    async def _build_tabs(self, groups: list[MediaListGroup]) -> None:
        self._entry_map = {}

        # Build a dict by status for easy lookup
        by_status = {g.status: g for g in groups}

        tabs = TabbedContent(id="list-tabs")
        await self.mount(tabs)

        for status, tab_label in STATUS_TAB_ORDER:
            group = by_status.get(status)
            entries = group.entries if group else []
            tab_id = f"tab-{status.lower()}"

            pane = TabPane(f"{tab_label} ({len(entries)})", id=tab_id)
            await tabs.add_pane(pane)

            if not entries:
                await pane.mount(Label(
                    f"No {tab_label.lower()} yet.",
                    classes="empty-msg",
                ))
                continue

            table = DataTable(id=f"table-{status.lower()}", cursor_type="row")
            await pane.mount(table)

            table.add_columns(
                "Title",
                "Progress",
                "Score",
                "Format",
                "Year",
                "Genres",
            )

            self._entry_map[status] = {}
            for entry in sorted(entries, key=lambda e: e.media.display_title):
                media = entry.media
                total = media.episodes if media.type == "ANIME" else media.chapters
                total_str = f"/{total}" if total else ""
                progress_str = f"{entry.progress}{total_str}"
                score_str = entry.display_score
                format_str = media.format or media.type
                year_str = str(media.season_year or media.year or "")
                genres_str = ", ".join(media.genres[:3]) if media.genres else ""

                row_key = str(media.id)
                table.add_row(
                    media.display_title[:45],
                    progress_str,
                    score_str,
                    format_str,
                    year_str,
                    genres_str,
                    key=row_key,
                )
                self._entry_map[status][row_key] = entry

    def _get_active_table_and_status(self) -> tuple[DataTable | None, str | None]:
        try:
            tabs = self.query_one("#list-tabs", TabbedContent)
            active_tab = tabs.active
            if not active_tab:
                return None, None
            # active is like "tab-current"
            status = active_tab.replace("tab-", "").upper()
            table_id = f"table-{active_tab.replace('tab-', '')}"
            table = self.query_one(f"#{table_id}", DataTable)
            return table, status
        except Exception:
            return None, None

    def _get_selected_entry(self) -> MediaList | None:
        table, status = self._get_active_table_and_status()
        if not table or not status:
            return None
        row_key = table.get_row_at(table.cursor_row)
        if row_key is None:
            return None
        # row_key is a RowKey; get its string value
        cursor_row = table.cursor_row
        try:
            row_key_obj = list(table.rows.keys())[cursor_row]
            return self._entry_map.get(status, {}).get(str(row_key_obj.value))
        except (IndexError, AttributeError):
            return None

    def action_edit_selected(self) -> None:
        entry = self._get_selected_entry()
        if entry is None:
            return
        from .edit_entry import EditEntryModal

        def on_result(result) -> None:
            self.run_worker(self._reload(), exclusive=True)

        self.app.push_screen(EditEntryModal(entry.media, entry), callback=on_result)

    def action_open_details(self) -> None:
        entry = self._get_selected_entry()
        if entry:
            from .details import MediaDetailsScreen
            self.app.push_screen(MediaDetailsScreen(entry.media.id))

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.action_open_details()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-anime":
            self._switch_type("ANIME")
        elif event.button.id == "btn-manga":
            self._switch_type("MANGA")

    def _switch_type(self, media_type: str) -> None:
        if self._current_type == media_type:
            return
        self._current_type = media_type

        # Update button styles
        try:
            anime_btn = self.query_one("#btn-anime", Button)
            manga_btn = self.query_one("#btn-manga", Button)
            if media_type == "ANIME":
                anime_btn.variant = "primary"
                manga_btn.variant = "default"
            else:
                anime_btn.variant = "default"
                manga_btn.variant = "primary"
        except Exception:
            pass

        self.run_worker(self._reload(), exclusive=True)

    async def _reload(self) -> None:
        try:
            old_tabs = self.query_one("#list-tabs", TabbedContent)
            await old_tabs.remove()
        except Exception:
            pass

        loading = LoadingIndicator(id="loading-list")
        await self.mount(loading)
        await self._load_lists()

    def action_refresh(self) -> None:
        self.run_worker(self._reload(), exclusive=True)
