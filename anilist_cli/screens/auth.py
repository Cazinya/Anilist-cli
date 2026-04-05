"""Login / authentication screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static

from ..api.auth import build_auth_url, exchange_code_for_token
from ..api.client import AnilistClient, AnilistError
from ..config import save_config


class LoginScreen(Screen):
    """Prompts the user to authenticate via AniList OAuth2 authorization code flow."""

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
    LoginScreen .field-label {
        color: $text;
        margin-top: 1;
        margin-bottom: 0;
    }
    LoginScreen #auth-url {
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
        overflow-x: auto;
    }
    LoginScreen #step2-note {
        color: $text-muted;
        margin-bottom: 1;
    }
    LoginScreen #error-msg {
        color: $error;
        margin-top: 1;
        display: none;
    }
    LoginScreen #login-btn {
        width: 100%;
        margin-top: 2;
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
                "[dim]Your app must be registered at "
                "https://anilist.co/settings/developer\n"
                "with redirect URI: https://anilist.co/api/v2/oauth/pin[/dim]",
                id="setup-note",
            )

            yield Static("Client ID", classes="field-label")
            yield Input(
                value=self.app.config.client_id,
                placeholder="Your AniList client ID",
                id="client-id-input",
            )

            yield Static("Client Secret", classes="field-label")
            yield Input(
                placeholder="Your AniList client secret",
                password=True,
                id="client-secret-input",
            )

            yield Static(
                "\nStep 1 — Open this URL in your browser to authorize:",
                classes="field-label",
            )
            yield Static(auth_url, id="auth-url")

            yield Static(
                "Step 2 — After authorizing, the PIN page shows an authorization code.\n"
                "         Paste that code below.",
                id="step2-note",
            )
            yield Input(
                placeholder="Paste the authorization code from the PIN page…",
                id="code-input",
            )

            yield Static("", id="error-msg")
            yield Button("Login", variant="primary", id="login-btn")
            yield Static("Press [bold]Escape[/bold] to quit", classes="hint")

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "client-id-input":
            # Regenerate the auth URL whenever the client ID changes
            new_url = build_auth_url(event.value.strip() or self.app.config.client_id)
            self.query_one("#auth-url", Static).update(new_url)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "login-btn":
            await self._do_login()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "code-input":
            await self._do_login()

    async def _do_login(self) -> None:
        client_id = self.query_one("#client-id-input", Input).value.strip()
        client_secret = self.query_one("#client-secret-input", Input).value.strip()
        code = self.query_one("#code-input", Input).value.strip()
        error_label = self.query_one("#error-msg", Static)

        if not client_id:
            error_label.update("Please enter your Client ID.")
            error_label.display = True
            return
        if not client_secret:
            error_label.update("Please enter your Client Secret.")
            error_label.display = True
            return
        if not code:
            error_label.update("Please paste the authorization code from the PIN page.")
            error_label.display = True
            return

        error_label.display = False
        login_btn = self.query_one("#login-btn", Button)
        login_btn.disabled = True
        login_btn.label = "Exchanging code…"

        try:
            token = await exchange_code_for_token(code, client_id, client_secret)

            login_btn.label = "Verifying…"
            api_client = AnilistClient(token)
            user = await api_client.get_viewer()

            # Persist to config
            self.app.config.access_token = token
            self.app.config.client_id = client_id
            self.app.config.client_secret = client_secret
            save_config(self.app.config)
            self.app.api_client = api_client
            self.app.current_user = user
            self.app.notify(f"Welcome, {user.name}!", severity="information")
            self.app.switch_mode("home")

        except ValueError as e:
            error_label.update(str(e))
            error_label.display = True
            login_btn.disabled = False
            login_btn.label = "Login"
        except AnilistError as e:
            error_label.update(f"API error: {e}")
            error_label.display = True
            login_btn.disabled = False
            login_btn.label = "Login"
        except Exception as e:
            error_label.update(f"Unexpected error: {e}")
            error_label.display = True
            login_btn.disabled = False
            login_btn.label = "Login"
