"""Data models for AniList users."""

from dataclasses import dataclass, field


@dataclass
class GenreStats:
    genre: str
    count: int
    mean_score: float
    minutes_watched: int = 0
    chapters_read: int = 0


@dataclass
class TagStats:
    tag: str
    count: int
    mean_score: float


@dataclass
class UserStats:
    # Anime stats
    anime_count: int = 0
    anime_mean_score: float = 0.0
    anime_minutes_watched: int = 0
    anime_episodes_watched: int = 0
    # Manga stats
    manga_count: int = 0
    manga_mean_score: float = 0.0
    manga_chapters_read: int = 0
    manga_volumes_read: int = 0
    # Status counts - anime
    anime_watching: int = 0
    anime_completed: int = 0
    anime_paused: int = 0
    anime_dropped: int = 0
    anime_planning: int = 0
    # Status counts - manga
    manga_reading: int = 0
    manga_completed: int = 0
    manga_paused: int = 0
    manga_dropped: int = 0
    manga_planning: int = 0
    # Top genres/tags
    top_anime_genres: list[GenreStats] = field(default_factory=list)
    top_manga_genres: list[GenreStats] = field(default_factory=list)
    top_tags: list[TagStats] = field(default_factory=list)

    @property
    def anime_days_watched(self) -> float:
        return round(self.anime_minutes_watched / 1440, 1)


@dataclass
class User:
    id: int
    name: str
    avatar_medium: str | None = None
    avatar_large: str | None = None
    banner_image: str | None = None
    about: str | None = None
    site_url: str | None = None
    created_at: int | None = None
    updated_at: int | None = None
    stats: UserStats | None = None

    @property
    def avatar_url(self) -> str | None:
        return self.avatar_large or self.avatar_medium
