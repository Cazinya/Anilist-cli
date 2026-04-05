"""Media details screen."""

from __future__ import annotations

import re

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, LoadingIndicator, Static

from ..models.media import Media, MediaList
from ..widgets.cover_image import CoverImage


def _strip_html(text: str) -> str:
    """Remove basic HTML tags from description text."""
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<i>(.*?)</i>", r"[italic]\1[/italic]", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<b>(.*?)</b>", r"[bold]\1[/bold]", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def _score_color(score: float | None) -> str:
    if score is None:
        return "$text-muted"
    val = score / 10
    if val >= 7.5:
        return "green"
    if val >= 5.0:
        return "yellow"
    return "red"


class MediaDetailsScreen(Screen):
    """Full media details view with cover image, info, and list management."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("a", "add_to_list", "Add/Edit list"),
        Binding("e", "add_to_list", "Edit entry", show=False),
        Binding("q", "go_back", "Back", show=False),
    ]

    DEFAULT_CSS = """
    MediaDetailsScreen {
        layout: vertical;
        background: $background;
    }
    MediaDetailsScreen #details-loading {
        height: 1fr;
    }
    MediaDetailsScreen #details-content {
        layout: horizontal;
        height: 1fr;
    }
    MediaDetailsScreen #left-panel {
        width: 26;
        min-width: 26;
        layout: vertical;
        padding: 1;
        background: $panel;
        border-right: tall $panel-lighten-1;
    }
    MediaDetailsScreen #right-panel {
        width: 1fr;
        layout: vertical;
        padding: 1 2;
        overflow-y: auto;
    }
    MediaDetailsScreen .detail-title {
        text-style: bold;
        color: $text;
        margin-bottom: 0;
    }
    MediaDetailsScreen .detail-native {
        color: $text-muted;
        margin-bottom: 1;
    }
    MediaDetailsScreen .section-header {
        text-style: bold;
        color: $accent;
        margin-top: 1;
        margin-bottom: 0;
    }
    MediaDetailsScreen .stat-label {
        color: $text-muted;
    }
    MediaDetailsScreen .stat-value {
        color: $text;
        text-style: bold;
    }
    MediaDetailsScreen .genre-pill {
        background: $boost;
        color: $accent;
        padding: 0 1;
        margin: 0 1 1 0;
    }
    MediaDetailsScreen .description-text {
        color: $text;
        margin-top: 1;
    }
    MediaDetailsScreen #action-bar {
        height: 3;
        layout: horizontal;
        background: $panel;
        padding: 0 2;
        align-vertical: middle;
    }
    MediaDetailsScreen #action-bar Button {
        margin-right: 1;
    }
    MediaDetailsScreen .list-status-badge {
        color: $success;
        text-style: bold;
        margin-left: 2;
        content-align: center middle;
    }
    """

    def __init__(self, media_id: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._media_id = media_id
        self._media: Media | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield LoadingIndicator(id="details-loading")
        yield Footer()

    def on_mount(self) -> None:
        self.run_worker(self._load_details(), name="load_details", exclusive=True)

    async def _load_details(self) -> None:
        try:
            media = await self.app.api_client.get_media_details(self._media_id)
            self._media = media

            loading = self.query_one("#details-loading", LoadingIndicator)
            await loading.remove()

            await self._render_details(media)
        except Exception as e:
            try:
                loading = self.query_one("#details-loading", LoadingIndicator)
                await loading.remove()
            except Exception:
                pass
            await self.mount(Label(f"[red]Failed to load details: {e}[/red]"))

    async def _render_details(self, media: Media) -> None:
        # Action bar
        action_bar = Static(id="action-bar")
        await self.mount(action_bar)

        if media.list_status:
            list_label = f"  List: [bold]{self._status_display(media.list_status, media.type)}[/bold]"
            if media.list_progress is not None:
                total = media.episodes if media.type == "ANIME" else media.chapters
                total_str = f"/{total}" if total else ""
                list_label += f"  Progress: [bold]{media.list_progress}{total_str}[/bold]"
            if media.list_score:
                list_label += f"  Score: [bold]{media.list_score / 10:.1f}[/bold]"
            await action_bar.mount(
                Button(
                    "Edit List Entry [E]",
                    variant="success",
                    id="edit-list-btn",
                )
            )
            await action_bar.mount(Static(list_label, classes="list-status-badge"))
        else:
            await action_bar.mount(
                Button("Add to List [A]", variant="primary", id="add-list-btn")
            )

        # Main content
        content = Horizontal(id="details-content")
        await self.mount(content)

        # Left panel
        left = Vertical(id="left-panel")
        await content.mount(left)

        await left.mount(
            CoverImage(
                url=media.cover_url,
                title=media.display_title,
                width=22,
                height=28,
                show_images=self.app.config.show_images,
            )
        )

        # Quick stats on left
        score_val = f"{media.score / 10:.1f}" if media.score else "N/A"
        score_color = _score_color(media.score)
        await left.mount(Static(f"★ [{score_color}]{score_val}[/{score_color}] / 10.0", classes="stat-value"))

        fmt = media.format or media.type
        await left.mount(Static(f"[dim]{fmt}[/dim]", classes="stat-label"))

        ep_label = "Episodes" if media.type == "ANIME" else "Chapters"
        ep_val = str(media.episodes or media.chapters or "?")
        await left.mount(Static(f"{ep_label}: [bold]{ep_val}[/bold]", classes="stat-label"))

        if media.season and media.season_year:
            await left.mount(
                Static(f"{media.season.capitalize()} {media.season_year}", classes="stat-label")
            )
        elif media.year:
            await left.mount(Static(f"Year: {media.year}", classes="stat-label"))

        status = (media.status or "").replace("_", " ").title()
        await left.mount(Static(f"Status: [bold]{status}[/bold]", classes="stat-label"))

        if media.studios:
            await left.mount(Static(f"Studio: {', '.join(media.studios[:2])}", classes="stat-label"))

        # Right panel
        right = ScrollableContainer(id="right-panel")
        await content.mount(right)

        # Titles
        display_title = media.display_title
        await right.mount(Static(f"[bold]{display_title}[/bold]", classes="detail-title"))
        if media.title_romaji and media.title_romaji != display_title:
            await right.mount(Static(media.title_romaji, classes="detail-native"))
        if media.title_native:
            await right.mount(Static(media.title_native, classes="detail-native"))

        # Genres
        if media.genres:
            await right.mount(Static("Genres", classes="section-header"))
            genre_row = Horizontal()
            await right.mount(genre_row)
            for genre in media.genres:
                await genre_row.mount(Static(genre, classes="genre-pill"))

        # Description
        if media.description:
            await right.mount(Static("Synopsis", classes="section-header"))
            desc = _strip_html(media.description)
            await right.mount(Static(desc[:2000], classes="description-text"))

        # Tags
        if media.tags:
            await right.mount(Static("Tags", classes="section-header"))
            tag_str = "  ".join(f"[dim]{t}[/dim]" for t in media.tags[:15])
            await right.mount(Static(tag_str, classes="description-text"))

        # Characters
        if media.characters:
            await right.mount(Static("Characters", classes="section-header"))
            char_lines = []
            for char in media.characters[:12]:
                role = char.role.capitalize()
                char_lines.append(f"  [bold]{char.name_full}[/bold] [dim]({role})[/dim]")
            await right.mount(Static("\n".join(char_lines), classes="description-text"))

    def _status_display(self, status: str, media_type: str) -> str:
        mapping = {
            "CURRENT": "Watching" if media_type == "ANIME" else "Reading",
            "COMPLETED": "Completed",
            "PAUSED": "On Hold",
            "DROPPED": "Dropped",
            "PLANNING": "Plan to Watch" if media_type == "ANIME" else "Plan to Read",
            "REPEATING": "Rewatching" if media_type == "ANIME" else "Rereading",
        }
        return mapping.get(status, status)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id in ("add-list-btn", "edit-list-btn"):
            self.action_add_to_list()

    def action_add_to_list(self) -> None:
        if not self._media:
            return
        from .edit_entry import EditEntryModal
        from ..models.media import MediaList

        existing: MediaList | None = None
        if self._media.list_entry_id is not None:
            existing = MediaList(
                id=self._media.list_entry_id,
                media=self._media,
                status=self._media.list_status or "PLANNING",
                progress=self._media.list_progress or 0,
                score=self._media.list_score or 0.0,
                notes=self._media.list_notes,
            )

        def on_saved(result) -> None:
            self.app.notify("List entry saved!", severity="information")
            # Reload details to refresh list status
            self.run_worker(self._reload_details(), exclusive=True)

        self.app.push_screen(EditEntryModal(self._media, existing), callback=on_saved)

    async def _reload_details(self) -> None:
        try:
            media = await self.app.api_client.get_media_details(self._media_id)
            self._media = media
            # Refresh action bar
            try:
                old_bar = self.query_one("#action-bar")
                await old_bar.remove()
            except Exception:
                pass
            try:
                old_content = self.query_one("#details-content")
                await old_content.remove()
            except Exception:
                pass
            await self._render_details(media)
        except Exception:
            pass

    def action_go_back(self) -> None:
        self.app.pop_screen()
