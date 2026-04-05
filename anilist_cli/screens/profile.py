"""Profile screen — user statistics and favorites."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, LoadingIndicator, Static

from ..models.user import User, UserStats
from ..widgets.cover_image import CoverImage
from ..widgets.stats_panel import StatsPanel
from ..config import clear_auth


class ProfileScreen(Screen):
    """Displays the current user's profile and statistics."""

    BINDINGS = [
        Binding("1", "app.switch_mode('home')", "Home", show=False),
        Binding("2", "app.switch_mode('search')", "Search", show=False),
        Binding("3", "app.switch_mode('my_list')", "My List", show=False),
        Binding("q", "app.quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
    ]

    DEFAULT_CSS = """
    ProfileScreen {
        layout: vertical;
        background: $background;
    }
    ProfileScreen #profile-loading {
        height: 1fr;
    }
    ProfileScreen #profile-header {
        layout: horizontal;
        height: 12;
        background: $panel;
        padding: 1 2;
        border-bottom: tall $panel-lighten-1;
    }
    ProfileScreen #avatar-area {
        width: 14;
        min-width: 14;
    }
    ProfileScreen #user-info {
        width: 1fr;
        layout: vertical;
        padding: 0 2;
    }
    ProfileScreen #username {
        text-style: bold;
        color: $text;
        margin-bottom: 0;
    }
    ProfileScreen #user-meta {
        color: $text-muted;
        margin-bottom: 1;
    }
    ProfileScreen #about-text {
        color: $text;
        margin-bottom: 1;
    }
    ProfileScreen #header-actions {
        width: auto;
        layout: vertical;
        align-horizontal: right;
    }
    ProfileScreen #stats-scroll {
        height: 1fr;
        overflow-y: auto;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield LoadingIndicator(id="profile-loading")
        yield Footer()

    def on_mount(self) -> None:
        self.run_worker(self._load_profile(), name="load_profile", exclusive=True)

    async def _load_profile(self) -> None:
        if not self.app.current_user:
            try:
                loading = self.query_one("#profile-loading", LoadingIndicator)
                await loading.remove()
            except Exception:
                pass
            await self.mount(Label("[red]Not logged in.[/red]"))
            return

        try:
            stats = await self.app.api_client.get_user_stats(self.app.current_user.id)
            self.app.current_user.stats = stats

            try:
                loading = self.query_one("#profile-loading", LoadingIndicator)
                await loading.remove()
            except Exception:
                pass

            await self._render_profile(self.app.current_user)
        except Exception as e:
            try:
                loading = self.query_one("#profile-loading", LoadingIndicator)
                await loading.remove()
            except Exception:
                pass
            await self.mount(Label(f"[red]Failed to load profile: {e}[/red]"))

    async def _render_profile(self, user: User) -> None:
        # Header section
        header = Horizontal(id="profile-header")
        await self.mount(header)

        # Avatar
        avatar_area = Vertical(id="avatar-area")
        await header.mount(avatar_area)
        await avatar_area.mount(
            CoverImage(
                url=user.avatar_url,
                title=user.name,
                width=12,
                height=10,
                show_images=self.app.config.show_images,
            )
        )

        # User info
        info = Vertical(id="user-info")
        await header.mount(info)
        await info.mount(Static(f"[bold]{user.name}[/bold]", id="username"))

        if user.site_url:
            await info.mount(Static(user.site_url, id="user-meta"))

        if user.about:
            # Strip HTML from about text
            import re
            about = re.sub(r"<[^>]+>", "", user.about)[:200]
            await info.mount(Static(about, id="about-text"))

        # Actions
        actions = Vertical(id="header-actions")
        await header.mount(actions)
        await actions.mount(Button("Logout", variant="error", id="logout-btn"))

        # Stats section
        if user.stats:
            scroll = ScrollableContainer(id="stats-scroll")
            await self.mount(scroll)
            await scroll.mount(StatsPanel(user.stats))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "logout-btn":
            self._do_logout()

    def _do_logout(self) -> None:
        self.app.config = clear_auth(self.app.config)
        self.app.api_client = None
        self.app.current_user = None
        from .auth import LoginScreen
        self.app.push_screen(LoginScreen())

    def action_refresh(self) -> None:
        self.run_worker(self._reload(), exclusive=True)

    async def _reload(self) -> None:
        try:
            old_header = self.query_one("#profile-header")
            await old_header.remove()
        except Exception:
            pass
        try:
            old_scroll = self.query_one("#stats-scroll")
            await old_scroll.remove()
        except Exception:
            pass

        loading = LoadingIndicator(id="profile-loading")
        await self.mount(loading)
        await self._load_profile()
