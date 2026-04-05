"""Data models for AniList media."""

from dataclasses import dataclass, field


@dataclass
class Character:
    id: int
    name_full: str
    name_native: str | None
    image_url: str | None
    role: str  # MAIN, SUPPORTING, BACKGROUND


@dataclass
class Media:
    id: int
    title_romaji: str
    title_english: str | None = None
    title_native: str | None = None
    type: str = "ANIME"          # ANIME | MANGA
    format: str | None = None    # TV, MOVIE, OVA, MANGA, NOVEL, etc.
    status: str | None = None    # FINISHED, RELEASING, NOT_YET_RELEASED, CANCELLED
    description: str | None = None
    episodes: int | None = None
    chapters: int | None = None
    volumes: int | None = None
    duration: int | None = None  # episode duration in minutes
    score: float | None = None   # average score out of 100
    genres: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    cover_image_medium: str | None = None
    cover_image_large: str | None = None
    cover_image_extra_large: str | None = None
    banner_image: str | None = None
    season: str | None = None    # WINTER, SPRING, SUMMER, FALL
    season_year: int | None = None
    year: int | None = None
    popularity: int = 0
    favourites: int = 0
    studios: list[str] = field(default_factory=list)
    characters: list["Character"] = field(default_factory=list)
    source: str | None = None    # ORIGINAL, MANGA, NOVEL, etc.
    country: str | None = None
    is_adult: bool = False
    site_url: str | None = None
    # User's list entry for this media (if authenticated)
    list_entry_id: int | None = None
    list_status: str | None = None
    list_progress: int | None = None
    list_score: float | None = None
    list_notes: str | None = None

    @property
    def display_title(self) -> str:
        return self.title_english or self.title_romaji

    @property
    def display_score(self) -> str:
        if self.score is None:
            return "N/A"
        return f"{self.score / 10:.1f}"

    @property
    def score_out_of_100(self) -> float | None:
        return self.score

    @property
    def cover_url(self) -> str | None:
        return (
            self.cover_image_extra_large
            or self.cover_image_large
            or self.cover_image_medium
        )

    @property
    def episode_or_chapter_count(self) -> str:
        if self.type == "ANIME":
            return str(self.episodes) if self.episodes else "?"
        return str(self.chapters) if self.chapters else "?"

    @property
    def progress_label(self) -> str:
        return "Episodes" if self.type == "ANIME" else "Chapters"


@dataclass
class MediaList:
    id: int
    media: Media
    status: str           # CURRENT, COMPLETED, PAUSED, DROPPED, PLANNING, REPEATING
    progress: int = 0
    score: float = 0.0    # user score 0-100
    notes: str | None = None
    repeat: int = 0
    private: bool = False
    started_at: str | None = None
    completed_at: str | None = None
    updated_at: int | None = None

    @property
    def display_score(self) -> str:
        if self.score == 0:
            return "-"
        return f"{self.score / 10:.1f}"

    @property
    def status_display(self) -> str:
        mapping = {
            "CURRENT": "Watching" if self.media.type == "ANIME" else "Reading",
            "COMPLETED": "Completed",
            "PAUSED": "On Hold",
            "DROPPED": "Dropped",
            "PLANNING": "Plan to Watch" if self.media.type == "ANIME" else "Plan to Read",
            "REPEATING": "Rewatching" if self.media.type == "ANIME" else "Rereading",
        }
        return mapping.get(self.status, self.status)


@dataclass
class MediaListGroup:
    name: str
    status: str
    entries: list[MediaList] = field(default_factory=list)
