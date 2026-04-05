"""Configuration and token management."""

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path


CONFIG_DIR = Path.home() / ".config" / "anilist-cli"
CONFIG_FILE = CONFIG_DIR / "config.json"
CACHE_DIR = Path.home() / ".cache" / "anilist-cli"
IMAGE_CACHE_DIR = CACHE_DIR / "images"

# Default AniList client ID for the implicit grant flow.
# Users should register their own at https://anilist.co/settings/developer
# and set it via ANILIST_CLIENT_ID environment variable or the config file.
DEFAULT_CLIENT_ID = "38485"  # AnilistTUI client


@dataclass
class Config:
    access_token: str = ""
    client_id: str = DEFAULT_CLIENT_ID
    show_images: bool = True
    score_format: str = "POINT_10_DECIMAL"  # POINT_100, POINT_10_DECIMAL, POINT_10, POINT_5, POINT_3, SMILEY

    def is_authenticated(self) -> bool:
        return bool(self.access_token)


def ensure_dirs() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> Config:
    ensure_dirs()
    if not CONFIG_FILE.exists():
        return Config()
    try:
        with open(CONFIG_FILE) as f:
            data = json.load(f)
        return Config(**{k: v for k, v in data.items() if k in Config.__dataclass_fields__})
    except (json.JSONDecodeError, TypeError):
        return Config()


def save_config(config: Config) -> None:
    ensure_dirs()
    with open(CONFIG_FILE, "w") as f:
        json.dump(asdict(config), f, indent=2)


def clear_auth(config: Config) -> Config:
    config.access_token = ""
    save_config(config)
    return config


def get_client_id() -> str:
    return os.environ.get("ANILIST_CLIENT_ID", DEFAULT_CLIENT_ID)
