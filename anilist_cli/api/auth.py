"""OAuth2 implicit flow helpers for AniList authentication."""

from ..config import get_client_id

ANILIST_AUTH_URL = "https://anilist.co/api/v2/oauth/authorize"
# AniList's official PIN page for CLI/desktop apps — no server needed.
# Register your app at https://anilist.co/settings/developer and set
# the redirect URI to exactly this URL.
ANILIST_PIN_REDIRECT = "https://anilist.co/api/v2/oauth/pin"


def build_auth_url(client_id: str | None = None) -> str:
    cid = client_id or get_client_id()
    return (
        f"{ANILIST_AUTH_URL}"
        f"?client_id={cid}"
        f"&redirect_uri={ANILIST_PIN_REDIRECT}"
        f"&response_type=token"
    )
