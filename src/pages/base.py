"""Page router and base page class."""

from __future__ import annotations

import logging
from typing import Any, Callable

import customtkinter as ctk

logger = logging.getLogger("tadris_qa_system")


class PageRouter:
    """Manages navigation between pages, destroying the old page on each switch."""

    def __init__(self, root: ctk.CTk, content_frame: ctk.CTkFrame) -> None:
        self.root = root
        self.content_frame = content_frame
        self.current_page: ctk.CTkFrame | None = None
        self.pages: dict[str, Callable[..., ctk.CTkFrame]] = {}

    def register_page(self, name: str, factory: Callable[..., ctk.CTkFrame]) -> None:
        self.pages[name] = factory

    def navigate(self, page_name: str, **kwargs: Any) -> None:
        if self.current_page:
            self.current_page.pack_forget()
            self.current_page.destroy()

        if page_name in self.pages:
            kwargs["master"] = self.content_frame
            self.current_page = self.pages[page_name](**kwargs)
            self.current_page.pack(fill="both", expand=True)
        else:
            logger.error("Unknown page: %s", page_name)


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
