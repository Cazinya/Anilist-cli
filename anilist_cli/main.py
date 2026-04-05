"""CLI entry point for AniList CLI."""

from __future__ import annotations

import click

from .app import AnilistApp
from .config import CONFIG_FILE, load_config, clear_auth


@click.group(invoke_without_command=True)
@click.option(
    "--no-images",
    is_flag=True,
    default=False,
    help="Disable image rendering (useful for terminals without image support).",
)
@click.pass_context
def cli(ctx: click.Context, no_images: bool) -> None:
    """AniList CLI — Browse and manage your anime & manga lists from the terminal."""
    if ctx.invoked_subcommand is None:
        app = AnilistApp(show_images=not no_images)
        app.run()


@cli.command()
def logout() -> None:
    """Remove stored authentication token."""
    config = load_config()
    if not config.is_authenticated():
        click.echo("You are not currently logged in.")
        return
    clear_auth(config)
    click.echo("Logged out successfully. Your access token has been removed.")


@cli.command()
def config() -> None:
    """Show the path to the configuration file."""
    click.echo(f"Config file: {CONFIG_FILE}")
    cfg = load_config()
    click.echo(f"Authenticated: {cfg.is_authenticated()}")
    click.echo(f"Show images: {cfg.show_images}")
    click.echo(f"Score format: {cfg.score_format}")


if __name__ == "__main__":
    cli()
