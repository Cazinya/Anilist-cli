"""OAuth2 implicit flow helpers for AniList authentication."""

from ..config import get_client_id

ANILIST_AUTH_URL = "https://anilist.co/api/v2/oauth/authorize"


def build_auth_url(client_id: str | None = None) -> str:
    cid = client_id or get_client_id()
    return f"{ANILIST_AUTH_URL}?client_id={cid}&response_type=token"
