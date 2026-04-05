"""Async AniList GraphQL API client."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from ..models.media import Character, Media, MediaList, MediaListGroup
from ..models.user import GenreStats, TagStats, User, UserStats
from . import queries as q


GRAPHQL_URL = "https://graphql.anilist.co"


class AnilistError(Exception):
    """Raised when the AniList API returns an error."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class AnilistClient:
    """Async client for the AniList GraphQL API."""

    def __init__(self, token: str = ""):
        self._token = token
        self._headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if token:
            self._headers["Authorization"] = f"Bearer {token}"

    def set_token(self, token: str) -> None:
        self._token = token
        self._headers["Authorization"] = f"Bearer {token}"

    async def _request(self, query: str, variables: dict[str, Any] | None = None) -> dict:
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = {k: v for k, v in variables.items() if v is not None}

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    GRAPHQL_URL,
                    json=payload,
                    headers=self._headers,
                )
            except httpx.TimeoutException:
                raise AnilistError("Request timed out. Check your internet connection.")
            except httpx.NetworkError as e:
                raise AnilistError(f"Network error: {e}")

        if response.status_code == 429:
            raise AnilistError("Rate limited by AniList API. Please wait a moment.", 429)
        if response.status_code == 401:
            raise AnilistError("Unauthorized. Your access token may be invalid or expired.", 401)

        try:
            data = response.json()
        except Exception:
            raise AnilistError(f"Invalid JSON response (HTTP {response.status_code})")

        if "errors" in data:
            errors = data["errors"]
            msg = "; ".join(e.get("message", "Unknown error") for e in errors)
            raise AnilistError(msg, response.status_code)

        return data.get("data", {})

    # ------------------------------------------------------------------ #
    # User / Auth
    # ------------------------------------------------------------------ #

    async def get_viewer(self) -> User:
        data = await self._request(q.GET_VIEWER)
        return _parse_user(data["Viewer"])

    async def get_user_stats(self, user_id: int) -> UserStats:
        data = await self._request(q.GET_USER_STATISTICS, {"userId": user_id})
        return _parse_user_stats(data["User"]["statistics"])

    # ------------------------------------------------------------------ #
    # Media browsing
    # ------------------------------------------------------------------ #

    async def get_trending(
        self,
        media_type: str = "ANIME",
        page: int = 1,
        per_page: int = 20,
    ) -> list[Media]:
        data = await self._request(
            q.GET_TRENDING,
            {"type": media_type, "page": page, "perPage": per_page},
        )
        return [_parse_media(m) for m in data["Page"]["media"]]

    async def get_popular(
        self,
        media_type: str = "ANIME",
        page: int = 1,
        per_page: int = 20,
    ) -> list[Media]:
        data = await self._request(
            q.GET_POPULAR,
            {"type": media_type, "page": page, "perPage": per_page},
        )
        return [_parse_media(m) for m in data["Page"]["media"]]

    async def get_seasonal(
        self,
        season: str,
        year: int,
        page: int = 1,
        per_page: int = 20,
    ) -> list[Media]:
        data = await self._request(
            q.GET_SEASONAL,
            {"season": season, "seasonYear": year, "page": page, "perPage": per_page},
        )
        return [_parse_media(m) for m in data["Page"]["media"]]

    async def search_media(
        self,
        search: str | None = None,
        media_type: str | None = None,
        genre: str | None = None,
        status: str | None = None,
        format: str | None = None,
        sort: list[str] | None = None,
        season: str | None = None,
        season_year: int | None = None,
        page: int = 1,
        per_page: int = 20,
        is_adult: bool = False,
    ) -> tuple[list[Media], bool]:
        """Returns (media_list, has_next_page)."""
        variables: dict[str, Any] = {
            "search": search,
            "type": media_type,
            "genre": genre,
            "status": status,
            "format": format,
            "sort": sort or (["SEARCH_MATCH"] if search else ["POPULARITY_DESC"]),
            "season": season,
            "seasonYear": season_year,
            "page": page,
            "perPage": per_page,
            "isAdult": is_adult if is_adult else None,
        }
        data = await self._request(q.SEARCH_MEDIA, variables)
        page_data = data["Page"]
        media = [_parse_media(m) for m in page_data["media"]]
        has_next = page_data["pageInfo"]["hasNextPage"]
        return media, has_next

    async def get_media_details(self, media_id: int) -> Media:
        data = await self._request(q.GET_MEDIA_DETAILS, {"id": media_id})
        return _parse_media_detailed(data["Media"])

    # ------------------------------------------------------------------ #
    # User lists
    # ------------------------------------------------------------------ #

    async def get_media_list(
        self, user_id: int, media_type: str = "ANIME"
    ) -> list[MediaListGroup]:
        data = await self._request(
            q.GET_MEDIA_LIST_COLLECTION,
            {"userId": user_id, "type": media_type},
        )
        groups = []
        status_order = ["CURRENT", "REPEATING", "COMPLETED", "PAUSED", "DROPPED", "PLANNING"]
        raw_lists = data["MediaListCollection"]["lists"]

        # Build a dict keyed by status for ordering
        by_status: dict[str, MediaListGroup] = {}
        for lst in raw_lists:
            if lst.get("isCustomList"):
                continue
            status = lst.get("status") or "PLANNING"
            entries = [_parse_media_list_entry(e) for e in lst.get("entries", [])]
            by_status[status] = MediaListGroup(
                name=lst["name"], status=status, entries=entries
            )

        for s in status_order:
            if s in by_status:
                groups.append(by_status[s])

        return groups

    async def save_list_entry(
        self,
        media_id: int,
        status: str,
        progress: int = 0,
        score: float = 0.0,
        notes: str = "",
        entry_id: int | None = None,
        repeat: int = 0,
        private: bool = False,
    ) -> MediaList:
        variables: dict[str, Any] = {
            "mediaId": media_id,
            "status": status,
            "progress": progress,
            "score": score,
            "notes": notes or None,
            "repeat": repeat,
            "private": private,
        }
        if entry_id is not None:
            variables["id"] = entry_id
        data = await self._request(q.SAVE_MEDIA_LIST_ENTRY, variables)
        return _parse_saved_entry(data["SaveMediaListEntry"])

    async def delete_list_entry(self, entry_id: int) -> bool:
        data = await self._request(q.DELETE_MEDIA_LIST_ENTRY, {"id": entry_id})
        return data["DeleteMediaListEntry"]["deleted"]


# ------------------------------------------------------------------ #
# Parsing helpers
# ------------------------------------------------------------------ #

def _parse_media(m: dict) -> Media:
    title = m.get("title", {})
    cover = m.get("coverImage", {}) or {}
    studios_data = m.get("studios", {}) or {}
    studios = [s["name"] for s in studios_data.get("nodes", [])]
    tags = [t["name"] for t in (m.get("tags") or []) if not t.get("isMediaSpoiler")]
    start = m.get("startDate") or {}

    return Media(
        id=m["id"],
        title_romaji=title.get("romaji", "Unknown"),
        title_english=title.get("english"),
        title_native=title.get("native"),
        type=m.get("type", "ANIME"),
        format=m.get("format"),
        status=m.get("status"),
        episodes=m.get("episodes"),
        chapters=m.get("chapters"),
        volumes=m.get("volumes"),
        duration=m.get("duration"),
        score=m.get("meanScore"),
        genres=m.get("genres") or [],
        tags=tags,
        cover_image_medium=cover.get("medium"),
        cover_image_large=cover.get("large"),
        cover_image_extra_large=cover.get("extraLarge"),
        banner_image=m.get("bannerImage"),
        season=m.get("season"),
        season_year=m.get("seasonYear"),
        year=start.get("year"),
        popularity=m.get("popularity", 0),
        favourites=m.get("favourites", 0),
        studios=studios,
        source=m.get("source"),
        country=m.get("countryOfOrigin"),
        is_adult=m.get("isAdult", False),
        site_url=m.get("siteUrl"),
    )


def _parse_media_detailed(m: dict) -> Media:
    media = _parse_media(m)

    # Parse characters
    chars_data = (m.get("characters") or {}).get("edges", [])
    characters = []
    for edge in chars_data:
        node = edge.get("node", {})
        name = node.get("name", {})
        img = node.get("image", {}) or {}
        characters.append(Character(
            id=node["id"],
            name_full=name.get("full", ""),
            name_native=name.get("native"),
            image_url=img.get("large") or img.get("medium"),
            role=edge.get("role", "SUPPORTING"),
        ))
    media.characters = characters

    # Parse list entry if present
    entry = m.get("mediaListEntry")
    if entry:
        media.list_entry_id = entry.get("id")
        media.list_status = entry.get("status")
        media.list_progress = entry.get("progress")
        media.list_score = entry.get("score")
        media.list_notes = entry.get("notes")

    return media


def _parse_media_list_entry(e: dict) -> MediaList:
    media = _parse_media(e["media"])
    return MediaList(
        id=e["id"],
        media=media,
        status=e.get("status", "PLANNING"),
        progress=e.get("progress") or 0,
        score=e.get("score") or 0.0,
        notes=e.get("notes"),
        repeat=e.get("repeat") or 0,
        private=e.get("private", False),
        updated_at=e.get("updatedAt"),
    )


def _parse_saved_entry(e: dict) -> MediaList:
    media_data = e.get("media", {})
    title = media_data.get("title", {})
    media = Media(
        id=media_data.get("id", 0),
        title_romaji=title.get("romaji", ""),
        title_english=title.get("english"),
        type=media_data.get("type", "ANIME"),
        episodes=media_data.get("episodes"),
        chapters=media_data.get("chapters"),
    )
    return MediaList(
        id=e["id"],
        media=media,
        status=e.get("status", "PLANNING"),
        progress=e.get("progress") or 0,
        score=e.get("score") or 0.0,
        notes=e.get("notes"),
        repeat=e.get("repeat") or 0,
        private=e.get("private", False),
    )


def _parse_user(u: dict) -> User:
    avatar = u.get("avatar") or {}
    return User(
        id=u["id"],
        name=u["name"],
        avatar_medium=avatar.get("medium"),
        avatar_large=avatar.get("large"),
        banner_image=u.get("bannerImage"),
        about=u.get("about"),
        site_url=u.get("siteUrl"),
        created_at=u.get("createdAt"),
        updated_at=u.get("updatedAt"),
    )


def _parse_user_stats(stats: dict) -> UserStats:
    anime = stats.get("anime", {})
    manga = stats.get("manga", {})

    def get_status_count(statuses: list, status_name: str) -> int:
        for s in statuses:
            if s.get("status") == status_name:
                return s.get("count", 0)
        return 0

    anime_statuses = anime.get("statuses", [])
    manga_statuses = manga.get("statuses", [])

    top_anime_genres = [
        GenreStats(
            genre=g["genre"],
            count=g["count"],
            mean_score=g.get("meanScore", 0),
            minutes_watched=g.get("minutesWatched", 0),
        )
        for g in anime.get("genres", [])[:10]
    ]
    top_manga_genres = [
        GenreStats(
            genre=g["genre"],
            count=g["count"],
            mean_score=g.get("meanScore", 0),
            chapters_read=g.get("chaptersRead", 0),
        )
        for g in manga.get("genres", [])[:10]
    ]
    top_tags = [
        TagStats(
            tag=t["tag"]["name"],
            count=t["count"],
            mean_score=t.get("meanScore", 0),
        )
        for t in (anime.get("tags", []) or [])[:10]
    ]

    return UserStats(
        anime_count=anime.get("count", 0),
        anime_mean_score=anime.get("meanScore", 0),
        anime_minutes_watched=anime.get("minutesWatched", 0),
        anime_episodes_watched=anime.get("episodesWatched", 0),
        manga_count=manga.get("count", 0),
        manga_mean_score=manga.get("meanScore", 0),
        manga_chapters_read=manga.get("chaptersRead", 0),
        manga_volumes_read=manga.get("volumesRead", 0),
        anime_watching=get_status_count(anime_statuses, "CURRENT"),
        anime_completed=get_status_count(anime_statuses, "COMPLETED"),
        anime_paused=get_status_count(anime_statuses, "PAUSED"),
        anime_dropped=get_status_count(anime_statuses, "DROPPED"),
        anime_planning=get_status_count(anime_statuses, "PLANNING"),
        manga_reading=get_status_count(manga_statuses, "CURRENT"),
        manga_completed=get_status_count(manga_statuses, "COMPLETED"),
        manga_paused=get_status_count(manga_statuses, "PAUSED"),
        manga_dropped=get_status_count(manga_statuses, "DROPPED"),
        manga_planning=get_status_count(manga_statuses, "PLANNING"),
        top_anime_genres=top_anime_genres,
        top_manga_genres=top_manga_genres,
        top_tags=top_tags,
    )
