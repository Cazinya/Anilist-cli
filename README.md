# AniList CLI

A feature-rich terminal client for [AniList](https://anilist.co) built with [Python Textual](https://textual.textualize.io/) and [Rich](https://rich.readthedocs.io/). Browse trending anime and manga, manage your lists, and view detailed media info — all from your terminal.

## Features

- **Home screen** — Trending and Popular anime & manga grids
- **Search** — Full-text search with filters (genre, status, format, season, year, sort)
- **Media details** — Cover art, synopsis, genres, characters, tags, studio info
- **My List** — View and manage your CURRENT/COMPLETED/ON HOLD/DROPPED/PLANNING lists for both anime and manga
- **List editing** — Add, update, or delete list entries with status, progress, score, and notes
- **Profile** — User stats with bar-chart breakdown by status and genre
- **Cover image support** — Renders cover art in Kitty, Sixel, or Unicode fallback for unsupported terminals
- **Keyboard-first** — Vim-style navigation and keyboard shortcuts throughout

## Installation

```bash
pip install -e .
```

Or with dependencies directly:

```bash
pip install textual textual-image httpx click rich Pillow
pip install -e .
```

## Authentication

AniList CLI uses the OAuth2 implicit flow. To authenticate:

1. Run `anilist-cli` — you will be shown an authorization URL
2. Open the URL in your browser and log in to AniList
3. After authorizing, you'll be redirected to a page containing your access token in the URL fragment (`#access_token=...`)
4. Copy the token and paste it back into the CLI prompt

Your token is stored at `~/.config/anilist-cli/config.json` and is valid for 1 year.

> **Tip:** Register your own AniList API client at https://anilist.co/settings/developer and set `ANILIST_CLIENT_ID` env variable to use your own client ID.

## Usage

```bash
# Launch the TUI
anilist-cli

# Launch without image rendering
anilist-cli --no-images

# Log out (remove saved token)
anilist-cli logout

# Show config file location
anilist-cli config
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `1` | Home (Trending) |
| `2` | Search |
| `3` | My List |
| `4` | Profile |
| `q` / `Ctrl+Q` | Quit |
| `Escape` | Go back / close modal |
| `j` / `↓` | Move down |
| `k` / `↑` | Move up |
| `Tab` | Switch tabs |
| `/` | Focus search input |
| `Enter` | Select / open details |
| `e` | Edit list entry |
| `r` | Refresh current view |
| `?` | Show help |

## Image Support

Cover art is rendered automatically when your terminal supports it:

- **Kitty** — Full quality via Kitty Graphics Protocol
- **iTerm2 / WezTerm** — Inline images
- **Sixel terminals** (e.g. xterm with sixel, mlterm) — Sixel graphics
- **Other terminals** — Unicode block character fallback

Use `--no-images` to disable image loading entirely.

Images are cached in `~/.cache/anilist-cli/images/`.

## Requirements

- Python 3.10+
- textual >= 0.70.0
- textual-image >= 0.5.0
- httpx >= 0.27.0
- click >= 8.1.0
- rich >= 13.0.0
- Pillow >= 10.0.0
