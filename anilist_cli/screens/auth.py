"""Login / authentication screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static

from ..api.auth import build_auth_url
from ..api.client import AnilistClient, AnilistError
from ..config import save_config


class LoginScreen(Screen):
    """Prompts the user to authenticate via AniList OAuth2 implicit flow."""

    BINDINGS = [
        Binding("escape", "app.quit", "Quit"),
    ]

    DEFAULT_CSS = """
    LoginScreen {
        align: center middle;
        background: $background;
    }
    LoginScreen #login-box {
        width: 76;
        height: auto;
        border: double $accent;
        background: $surface;
        padding: 2 4;
        layout: vertical;
    }
    LoginScreen #title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    LoginScreen #subtitle {
        text-align: center;
        color: $text-muted;
        margin-bottom: 2;
    }
    LoginScreen #setup-note {
        color: $text-muted;
        background: $boost;
        padding: 1 2;
        margin-bottom: 2;
    }
    LoginScreen #step-label {
        color: $text;
        margin-bottom: 1;
    }
    LoginScreen #auth-url {
        color: $accent;
        text-style: underline;
        margin-bottom: 2;
        overflow-x: auto;
    }
    LoginScreen #token-label {
        color: $text;
        margin-bottom: 1;
    }
    LoginScreen #token-input {
        margin-bottom: 1;
    }
    LoginScreen #error-msg {
        color: $error;
        margin-bottom: 1;
        display: none;
    }
    LoginScreen #login-btn {
        width: 100%;
        margin-top: 1;
    }
    LoginScreen .hint {
        color: $text-muted;
        text-align: center;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        auth_url = build_auth_url(self.app.config.client_id)
        with Static(id="login-box"):
            yield Static("AniList CLI", id="title")
            yield Static("Connect your AniList account to get started", id="subtitle")
            yield Static(
                "[dim]Requires an AniList API client with redirect URI set to:[/dim]\n"
                "[bold]https://anilist.co/api/v2/oauth/pin[/bold]\n"
                "[dim]Register at: https://anilist.co/settings/developer[/dim]",
                id="setup-note",
            )
            yield Static("Step 1 — Open this URL in your browser to authorize:", id="step-label")
            yield Static(auth_url, id="auth-url")
            yield Static(
                "Step 2 — After authorizing, you will be shown your access token.\n"
                "         Copy it and paste it below.",
                id="token-label",
            )
            yield Input(
                placeholder="Paste your access token here…",
                id="token-input",
            )
            yield Static("", id="error-msg")
            yield Button("Login", variant="primary", id="login-btn")
            yield Static("Press [bold]Escape[/bold] to quit", classes="hint")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "login-btn":
            await self._do_login()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        await self._do_login()

    async def _do_login(self) -> None:
        token_input = self.query_one("#token-input", Input)
        error_label = self.query_one("#error-msg", Static)
        token = token_input.value.strip()

        if not token:
            error_label.update("Please enter your access token.")
            error_label.display = True
            return

        error_label.display = False
        login_btn = self.query_one("#login-btn", Button)
        login_btn.disabled = True
        login_btn.label = "Verifying…"

        try:
            client = AnilistClient(token)
            user = await client.get_viewer()

            # Persist token and set app state
            self.app.config.access_token = token
            save_config(self.app.config)
            self.app.api_client = client
            self.app.current_user = user
            self.app.notify(f"Welcome, {user.name}!", severity="information")
            self.app.switch_mode("home")
        except AnilistError as e:
            error_label.update(f"Login failed: {e}")
            error_label.display = True
            login_btn.disabled = False
            login_btn.label = "Login"
        except Exception as e:
            error_label.update(f"Unexpected error: {e}")
            error_label.display = True
            login_btn.disabled = False
            login_btn.label = "Login"
