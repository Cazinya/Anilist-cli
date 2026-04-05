"""Cover image widget with terminal image protocol support and fallback."""

from __future__ import annotations

import hashlib
from pathlib import Path

import httpx
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from ..config import IMAGE_CACHE_DIR


class CoverImage(Widget):
    """
    Displays media cover art.

    Uses textual-image AutoImage (auto-detects Kitty/Sixel/Unicode half-block)
    when available. Falls back to a styled text placeholder on any error.
    """

    DEFAULT_CSS = """
    CoverImage {
        width: auto;
        height: auto;
    }
    CoverImage .placeholder {
        background: $boost;
        color: $text-muted;
        text-align: center;
        content-align: center middle;
        border: tall $panel-lighten-2;
    }
    CoverImage AutoImage, CoverImage TGPImage, CoverImage SixelImage,
    CoverImage HalfcellImage, CoverImage UnicodeImage {
        width: 100%;
        height: 100%;
    }
    """

    def __init__(
        self,
        url: str | None,
        title: str = "",
        width: int = 22,
        height: int = 30,
        show_images: bool = True,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._url = url
        self._title = title
        self._img_width = width
        self._img_height = height
        self._show_images = show_images
        self.styles.width = width
        self.styles.height = height

    def compose(self) -> ComposeResult:
        placeholder = Static(
            self._make_placeholder(),
            classes="placeholder",
            id="cover-placeholder",
        )
        placeholder.styles.width = self._img_width
        placeholder.styles.height = self._img_height
        yield placeholder

    def _make_placeholder(self) -> str:
        w = self._img_width - 2  # inside border
        h = self._img_height - 2
        title = (self._title or "No Image")[:w]
        lines = []
        for i in range(h):
            if i == h // 2:
                lines.append(title.center(w))
            else:
                lines.append("")
        return "\n".join(lines)

    def on_mount(self) -> None:
        if self._show_images and self._url:
            self.run_worker(self._load_image(), exclusive=True, name="cover_load")

    async def _load_image(self) -> None:
        try:
            image_path = await self._fetch_cached(self._url)
            if image_path is None:
                return
            await self._render_image(image_path)
        except Exception:
            pass  # Keep placeholder on any error

    async def _fetch_cached(self, url: str) -> Path | None:
        url_hash = hashlib.md5(url.encode()).hexdigest()
        suffix = url.split(".")[-1].split("?")[0].lower()
        if suffix not in ("jpg", "jpeg", "png", "webp", "gif"):
            suffix = "jpg"
        cache_path = IMAGE_CACHE_DIR / f"{url_hash}.{suffix}"

        if cache_path.exists() and cache_path.stat().st_size > 0:
            return cache_path

        try:
            IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                response = await client.get(url)
                if response.status_code == 200 and response.content:
                    cache_path.write_bytes(response.content)
                    return cache_path
        except Exception:
            pass
        return None

    async def _render_image(self, image_path: Path) -> None:
        try:
            from textual_image.widget import AutoImage

            # Open with PIL first so we can verify the file and control format
            from PIL import Image as PILImage
            pil_img = PILImage.open(image_path)
            pil_img.load()  # Force decode now to catch corrupt files

            img_widget = AutoImage(pil_img, id="cover-img")
            img_widget.styles.width = self._img_width
            img_widget.styles.height = self._img_height

            placeholder = self.query_one("#cover-placeholder", Static)
            await placeholder.remove()
            await self.mount(img_widget)
        except Exception:
            pass  # Keep placeholder
