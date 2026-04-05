"""OAuth2 authorization code flow helpers for AniList authentication."""

from __future__ import annotations

import httpx

from ..config import get_client_id

ANILIST_AUTH_URL = "https://anilist.co/api/v2/oauth/authorize"
ANILIST_TOKEN_URL = "https://anilist.co/api/v2/oauth/token"
# AniList's PIN page for CLI/desktop apps — displays the auth code after authorization.
# Set this as the redirect URI when registering your app.
ANILIST_PIN_REDIRECT = "https://anilist.co/api/v2/oauth/pin"


def build_auth_url(client_id: str | None = None) -> str:
    cid = client_id or get_client_id()
    return (
        f"{ANILIST_AUTH_URL}"
        f"?client_id={cid}"
        f"&redirect_uri={ANILIST_PIN_REDIRECT}"
        f"&response_type=code"
    )


async def exchange_code_for_token(
    code: str,
    client_id: str,
    client_secret: str,
) -> str:
    """Exchange an authorization code for an access token.

    Returns the access token string.
    Raises httpx.HTTPStatusError or ValueError on failure.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            ANILIST_TOKEN_URL,
            json={
                "grant_type": "authorization_code",
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": ANILIST_PIN_REDIRECT,
                "code": code,
            },
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )

    if response.status_code != 200:
        try:
            detail = response.json().get("message", response.text)
        except Exception:
            detail = response.text
        raise ValueError(f"Token exchange failed ({response.status_code}): {detail}")

    data = response.json()
    token = data.get("access_token")
    if not token:
        raise ValueError("No access_token in response.")
    return token
