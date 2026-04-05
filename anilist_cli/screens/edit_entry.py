"""Edit list entry modal screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, Static, TextArea

from ..api.client import AnilistError
from ..models.media import Media, MediaList


STATUS_OPTIONS_ANIME = [
    ("Watching", "CURRENT"),
    ("Completed", "COMPLETED"),
    ("On Hold", "PAUSED"),
    ("Dropped", "DROPPED"),
    ("Plan to Watch", "PLANNING"),
    ("Rewatching", "REPEATING"),
]

STATUS_OPTIONS_MANGA = [
    ("Reading", "CURRENT"),
    ("Completed", "COMPLETED"),
    ("On Hold", "PAUSED"),
    ("Dropped", "DROPPED"),
    ("Plan to Read", "PLANNING"),
    ("Rereading", "REPEATING"),
]


class EditEntryModal(ModalScreen):
    """Modal for adding or editing a media list entry."""

    BINDINGS = [
        Binding("escape", "dismiss", "Cancel"),
        Binding("ctrl+s", "save", "Save"),
    ]

    DEFAULT_CSS = """
    EditEntryModal {
        align: center middle;
    }
    EditEntryModal #modal-box {
        width: 60;
        height: auto;
        border: double $accent;
        background: $surface;
        padding: 2 4;
        layout: vertical;
    }
    EditEntryModal #modal-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    EditEntryModal #media-title {
        text-align: center;
        color: $text-muted;
        margin-bottom: 2;
    }
    EditEntryModal .field-label {
        color: $text;
        margin-top: 1;
        margin-bottom: 0;
    }
    EditEntryModal #error-msg {
        color: $error;
        margin-top: 1;
        display: none;
    }
    EditEntryModal #button-row {
        layout: horizontal;
        height: 3;
        margin-top: 2;
        align-horizontal: right;
    }
    EditEntryModal #save-btn {
        margin-right: 1;
    }
    """

    class Saved(Message):
        def __init__(self, entry: MediaList) -> None:
            super().__init__()
            self.entry = entry

    class Deleted(Message):
        def __init__(self, entry_id: int, media_id: int) -> None:
            super().__init__()
            self.entry_id = entry_id
            self.media_id = media_id

    def __init__(self, media: Media, existing_entry: MediaList | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._media = media
        self._existing = existing_entry

    def compose(self) -> ComposeResult:
        is_anime = self._media.type == "ANIME"
        status_opts = STATUS_OPTIONS_ANIME if is_anime else STATUS_OPTIONS_MANGA
        current_status = (self._existing.status if self._existing else "PLANNING")
        current_progress = str(self._existing.progress if self._existing else 0)
        current_score = str(
            round(self._existing.score / 10, 1) if self._existing and self._existing.score else 0.0
        )
        current_notes = self._existing.notes or "" if self._existing else ""

        progress_label = "Episode" if is_anime else "Chapter"
        total = self._media.episodes if is_anime else self._media.chapters
        total_str = f"/ {total}" if total else ""

        with Static(id="modal-box"):
            yield Static(
                "Edit Entry" if self._existing else "Add to List",
                id="modal-title",
            )
            yield Static(self._media.display_title[:50], id="media-title")

            yield Label("Status", classes="field-label")
            yield Select(
                status_opts,
                value=current_status,
                id="status-select",
            )

            yield Label(f"{progress_label} Progress {total_str}", classes="field-label")
            yield Input(
                value=current_progress,
                placeholder="0",
                id="progress-input",
            )

            yield Label("Score (0.0 – 10.0)", classes="field-label")
            yield Input(
                value=current_score,
                placeholder="0.0",
                id="score-input",
            )

            yield Label("Notes", classes="field-label")
            yield TextArea(
                text=current_notes,
                id="notes-input",
            )

            yield Static("", id="error-msg")

            with Static(id="button-row"):
                if self._existing:
                    yield Button("Delete", variant="error", id="delete-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")
                yield Button("Save", variant="primary", id="save-btn")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            await self.action_save()
        elif event.button.id == "cancel-btn":
            self.dismiss()
        elif event.button.id == "delete-btn":
            await self._do_delete()

    async def action_save(self) -> None:
        error_label = self.query_one("#error-msg", Static)
        error_label.display = False

        status_select = self.query_one("#status-select", Select)
        progress_input = self.query_one("#progress-input", Input)
        score_input = self.query_one("#score-input", Input)
        notes_input = self.query_one("#notes-input", TextArea)

        status = str(status_select.value) if status_select.value != Select.BLANK else "PLANNING"

        try:
            progress = int(progress_input.value or 0)
        except ValueError:
            error_label.update("Progress must be a whole number.")
            error_label.display = True
            return

        try:
            score_raw = float(score_input.value or 0)
            if not (0.0 <= score_raw <= 10.0):
                raise ValueError()
            score = score_raw * 10  # API uses 0-100
        except ValueError:
            error_label.update("Score must be between 0.0 and 10.0.")
            error_label.display = True
            return

        notes = notes_input.text.strip()

        save_btn = self.query_one("#save-btn", Button)
        save_btn.disabled = True
        save_btn.label = "Saving…"

        try:
            entry = await self.app.api_client.save_list_entry(
                media_id=self._media.id,
                status=status,
                progress=progress,
                score=score,
                notes=notes,
                entry_id=self._existing.id if self._existing else None,
            )
            self.post_message(self.Saved(entry))
            self.dismiss()
        except AnilistError as e:
            error_label.update(f"Save failed: {e}")
            error_label.display = True
            save_btn.disabled = False
            save_btn.label = "Save"

    async def _do_delete(self) -> None:
        if not self._existing:
            return
        delete_btn = self.query_one("#delete-btn", Button)
        delete_btn.disabled = True
        delete_btn.label = "Deleting…"
        try:
            await self.app.api_client.delete_list_entry(self._existing.id)
            self.post_message(self.Deleted(self._existing.id, self._media.id))
            self.dismiss()
        except AnilistError as e:
            error_label = self.query_one("#error-msg", Static)
            error_label.update(f"Delete failed: {e}")
            error_label.display = True
            delete_btn.disabled = False
            delete_btn.label = "Delete"
