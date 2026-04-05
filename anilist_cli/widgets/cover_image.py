"""Cover image widget with terminal image protocol support and fallback."""

from __future__ import annotations

import asyncio
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

    Uses textual-image for Kitty/Sixel/Unicode rendering when available.
    Falls back to a styled placeholder if images are disabled or unsupported.
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

    def compose(self) -> ComposeResult:
        yield Static(
            self._placeholder_text(),
            classes="placeholder",
            id="cover-placeholder",
        )

    def _placeholder_text(self) -> str:
        lines = ["╔" + "═" * (self._img_width - 2) + "╗"]
        mid = self._img_height - 2
        for i in range(mid):
            if i == mid // 2 and self._title:
                text = self._title[: self._img_width - 4]
                pad = (self._img_width - 2 - len(text)) // 2
                lines.append("║" + " " * pad + text + " " * (self._img_width - 2 - pad - len(text)) + "║")
            elif i == mid // 2 + 1:
                lines.append("║" + " [dim]No Image[/dim] ".center(self._img_width - 2) + "║")
            else:
                lines.append("║" + " " * (self._img_width - 2) + "║")
        lines.append("╚" + "═" * (self._img_width - 2) + "╝")
        return "\n".join(lines)

    async def on_mount(self) -> None:
        if self._show_images and self._url:
            self.run_worker(self._load_image(), exclusive=True)

    async def _load_image(self) -> None:
        try:
            image_path = await self._get_cached_image(self._url)
            if image_path is None:
                return
            await self._render_image(image_path)
        except Exception:
            pass  # Keep placeholder on any error

    async def _get_cached_image(self, url: str) -> Path | None:
        url_hash = hashlib.md5(url.encode()).hexdigest()
        ext = url.split(".")[-1].split("?")[0].lower()
        if ext not in ("jpg", "jpeg", "png", "webp", "gif"):
            ext = "jpg"
        cache_path = IMAGE_CACHE_DIR / f"{url_hash}.{ext}"

        if cache_path.exists():
            return cache_path

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, follow_redirects=True)
                if response.status_code == 200:
                    IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
                    cache_path.write_bytes(response.content)
                    return cache_path
        except Exception:
            pass
        return None

    async def _render_image(self, image_path: Path) -> None:
        try:
            from textual_image.widget import Image as TxImage

            placeholder = self.query_one("#cover-placeholder")
            await placeholder.remove()

            img_widget = TxImage(
                str(image_path),
                id="cover-img",
            )
            img_widget.styles.width = self._img_width
            img_widget.styles.height = self._img_height
            await self.mount(img_widget)
        except (ImportError, Exception):
            pass  # textual-image not available; keep placeholder
