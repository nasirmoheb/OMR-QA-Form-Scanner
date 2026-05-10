"""Page router and base page class."""

from __future__ import annotations

import logging
from typing import Any, Callable

import customtkinter as ctk

logger = logging.getLogger("tadris_qa_system")


class PageRouter:
    """Manages navigation between pages.

    Pages that are registered with ``cacheable=True`` are built once and
    reused on subsequent visits (show/hide via pack).  Pages that carry
    per-visit data (e.g. process, results) are still destroyed and rebuilt
    each time so they always reflect fresh kwargs.
    """

    def __init__(self, root: ctk.CTk, content_frame: ctk.CTkFrame) -> None:
        self.root = root
        self.content_frame = content_frame
        self.current_page: ctk.CTkFrame | None = None
        self.pages: dict[str, Callable[..., ctk.CTkFrame]] = {}
        self._cacheable: set[str] = set()
        self._cache: dict[str, ctk.CTkFrame] = {}

    def register_page(
        self,
        name: str,
        factory: Callable[..., ctk.CTkFrame],
        cacheable: bool = False,
    ) -> None:
        self.pages[name] = factory
        if cacheable:
            self._cacheable.add(name)

    def navigate(self, page_name: str, **kwargs: Any) -> None:
        # Hide the current page (don't destroy if it's cached)
        if self.current_page is not None:
            if hasattr(self.current_page, "_router_page_name") and \
                    self.current_page._router_page_name in self._cacheable:  # type: ignore[attr-defined]
                self.current_page.pack_forget()
            else:
                self.current_page.pack_forget()
                self.current_page.destroy()
            self.current_page = None

        if page_name not in self.pages:
            logger.error("Unknown page: %s", page_name)
            return

        # Return cached instance for cacheable pages (no kwargs needed on revisit)
        if page_name in self._cacheable and page_name in self._cache:
            page = self._cache[page_name]
            # Let the page refresh itself if it exposes on_show()
            if hasattr(page, "on_show"):
                page.on_show()  # type: ignore[attr-defined]
        else:
            kwargs["master"] = self.content_frame
            page = self.pages[page_name](**kwargs)
            page._router_page_name = page_name  # type: ignore[attr-defined]
            if page_name in self._cacheable:
                self._cache[page_name] = page

        page.pack(fill="both", expand=True)
        self.current_page = page

    def invalidate(self, page_name: str) -> None:
        """Destroy the cached instance of *page_name* so it rebuilds next visit."""
        cached = self._cache.pop(page_name, None)
        if cached is not None:
            try:
                cached.destroy()
            except Exception:
                pass


class BasePage(ctk.CTkFrame):
    """Base class for all pages."""

    def __init__(
        self,
        router: PageRouter,
        navigate_callback: Callable[[str, Any], None] | None = None,
        **kwargs: Any,
    ) -> None:
        # Remove fg_color default so subclasses can set PAGE_BG
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(**kwargs)
        self.router = router
        self.navigate_callback = navigate_callback

    def go(self, page: str, **kwargs: Any) -> None:
        """Convenience: navigate via callback or router."""
        if self.navigate_callback:
            self.navigate_callback(page, **kwargs)
        else:
            self.router.navigate(page, **kwargs)
