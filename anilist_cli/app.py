"""Main Textual application for AniList CLI."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding

from .api.client import AnilistClient
from .config import Config, load_config
from .models.user import User


class AnilistApp(App):
    """The main AniList CLI Textual application."""

    TITLE = "AniList CLI"
    SUB_TITLE = "Your anime & manga companion"

    BINDINGS = [
        Binding("1", "switch_mode('home')", "Home", priority=True),
        Binding("2", "switch_mode('search')", "Search", priority=True),
        Binding("3", "switch_mode('my_list')", "My List", priority=True),
        Binding("4", "switch_mode('profile')", "Profile", priority=True),
        Binding("ctrl+q", "quit", "Quit", priority=True),
    ]

    CSS = """
    /* Global theme overrides */
    Screen {
        background: $background;
    }

    Header {
        background: $panel;
        color: $accent;
    }

    Footer {
        background: $panel-darken-1;
        color: $text-muted;
    }

    /* Navigation mode indicator in footer */
    Footer .footer--key {
        background: $accent;
        color: $background;
    }

    /* Scrollbars */
    ScrollBar {
        background: $panel;
    }
    ScrollBar > .scrollbar--bar {
        background: $accent;
    }

    /* DataTable styling */
    DataTable {
        background: $surface;
    }
    DataTable > .datatable--header {
        background: $panel;
        color: $accent;
        text-style: bold;
    }
    DataTable > .datatable--cursor {
        background: $boost;
        color: $text;
    }

    /* TabbedContent */
    TabbedContent > TabPane {
        padding: 0;
    }
    Tabs > Tab {
        padding: 0 2;
    }
    Tabs > Tab.-active {
        color: $accent;
    }

    /* Buttons */
    Button.-primary {
        background: $accent;
        color: $background;
    }
    Button.-success {
        background: $success;
        color: $background;
    }

    /* Inputs */
    Input {
        background: $surface;
        border: tall $panel-lighten-1;
    }
    Input:focus {
        border: tall $accent;
    }

    /* Select dropdowns */
    Select {
        background: $surface;
    }
    SelectOverlay {
        background: $surface;
        border: tall $accent;
    }

    /* Loading */
    LoadingIndicator {
        color: $accent;
    }

    /* Notifications */
    Toast {
        background: $panel;
        border: tall $accent;
    }
    """

    MODES = {
        "login": "anilist_cli.screens.auth.LoginScreen",
        "home": "anilist_cli.screens.home.HomeScreen",
        "search": "anilist_cli.screens.search.SearchScreen",
        "my_list": "anilist_cli.screens.my_list.MyListScreen",
        "profile": "anilist_cli.screens.profile.ProfileScreen",
    }

    def __init__(self, show_images: bool = True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config: Config = load_config()
        self.config.show_images = show_images and self.config.show_images
        self.api_client: AnilistClient | None = None
        self.current_user: User | None = None

    def on_mount(self) -> None:
        if self.config.is_authenticated():
            self.api_client = AnilistClient(self.config.access_token)
            # Try to load the current user in the background
            self.run_worker(self._init_user(), name="init_user", exclusive=False)
            self.switch_mode("home")
        else:
            self.switch_mode("login")

    async def _init_user(self) -> None:
        """Silently fetch the current user on startup."""
        if self.api_client is None:
            return
        try:
            user = await self.api_client.get_viewer()
            self.current_user = user
        except Exception:
            pass  # Non-fatal; individual screens will handle missing user

    def action_switch_mode(self, mode: str) -> None:
        # Require authentication for protected modes
        if mode in ("home", "search", "my_list", "profile"):
            if not self.config.is_authenticated():
                self.switch_mode("login")
                return
        self.switch_mode(mode)
