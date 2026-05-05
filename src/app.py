"""Main application window — sidebar navigation + page routing."""

from __future__ import annotations

from typing import Any

import customtkinter as ctk

import icons as IC
import theme as T
from analytics_engine import AnalyticsEngine
from config import Config, setup_logging
from i18n import I18n, _
from pages import (
    PageRouter,
    DashboardPage,
    SurveyFormPage,
    ProcessPage,
    ResultsPage,
    SettingsFrame,
)
from persistence import PersistenceManager
from vision_processor import VisionProcessor

logger = setup_logging()

# Nav item: (page_id, icon_name, i18n_key)
_NAV_ITEMS = [
    ("dashboard",   "dashboard",  "dashboard"),
    ("survey_form", "plus",       "new_survey"),
    ("process",     "scan",       "process"),
    ("results",     "bar_chart",  "results"),
    ("settings",    "settings",   "settings"),
]

# Sidebar icon colour (inactive / active)
_NAV_ICON_COLOR         = "#64748B"
_NAV_ICON_COLOR_ACTIVE  = "#FFFFFF"


class OMRGUI:
    """Root application window: dark sidebar + dynamic content area."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()

        ctk.set_appearance_mode(self.config.APPEARANCE_MODE)
        I18n.set_language(self.config.LANGUAGE)

        self.persistence = PersistenceManager()
        self.vision      = VisionProcessor(config=self.config)
        self.analytics   = AnalyticsEngine(config=self.config)

        self.root = ctk.CTk()
        self.root.title(_("app_title"))
        self.root.geometry("1340x800")
        self.root.minsize(1100, 660)

        self._build()
        I18n.register_listener(self._on_lang_change)

    # ----
    # Build
    # ----

    def _build(self) -> None:
        root_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        root_frame.pack(fill="both", expand=True)

        self._build_sidebar(root_frame)
        self._build_content(root_frame)
        self._register_pages()
        self._navigate("dashboard")

    # -- Sidebar ----

    def _build_sidebar(self, parent: ctk.CTkFrame) -> None:
        self.sidebar = ctk.CTkFrame(
            parent,
            width=T.SIDEBAR_WIDTH,
            corner_radius=0,
            fg_color=T.SIDEBAR_BG,
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # -- App logo block ----
        logo_wrap = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_wrap.pack(fill="x", padx=18, pady=(24, 0))

        # Icon badge
        icon_sq = ctk.CTkFrame(
            logo_wrap, width=36, height=36,
            corner_radius=9, fg_color=T.ACCENT,
        )
        icon_sq.pack(side="left")
        icon_sq.pack_propagate(False)
        ctk.CTkLabel(
            icon_sq,
            image=IC.icon("omr", size=20, color="#FFFFFF"),
            text="",
        ).place(relx=0.5, rely=0.5, anchor="center")

        text_col = ctk.CTkFrame(logo_wrap, fg_color="transparent")
        text_col.pack(side="left", padx=(10, 0))
        ctk.CTkLabel(
            text_col,
            text="OMR Scanner",
            font=T.font(14, "bold"),
            text_color=T.SIDEBAR_TEXT_ACTIVE,
        ).pack(anchor="w")
        ctk.CTkLabel(
            text_col,
            text="QA Form System",
            font=T.tiny(),
            text_color=T.SIDEBAR_TEXT,
        ).pack(anchor="w")

        # -- Divider ----
        ctk.CTkFrame(
            self.sidebar, height=1, fg_color=T.SIDEBAR_BORDER
        ).pack(fill="x", padx=18, pady=(18, 12))

        # -- Nav buttons ----
        self._nav_btns: dict[str, ctk.CTkButton] = {}
        self._nav_pills: dict[str, ctk.CTkFrame] = {}

        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", padx=8)

        for page_id, icon_name, key in _NAV_ITEMS:
            label = _(key)
            row = ctk.CTkFrame(nav_frame, fg_color="transparent")
            row.pack(fill="x", pady=(0, 2))

            btn = ctk.CTkButton(
                row,
                image=IC.icon(icon_name, size=16, color=_NAV_ICON_COLOR),
                text=f"  {label}",
                font=T.font(13),
                height=44,
                corner_radius=T.RADIUS_MD,
                fg_color="transparent",
                hover_color=T.SIDEBAR_HOVER_BG,
                text_color=T.SIDEBAR_TEXT,
                anchor="w",
                compound="left",
                command=lambda pid=page_id: self._navigate(pid),
            )
            btn.pack(side="left", fill="x", expand=True)
            self._nav_btns[page_id] = btn

            # Right-side active indicator pill
            pill = ctk.CTkFrame(
                row, width=4, height=28, corner_radius=2, fg_color="transparent",
            )
            pill.pack(side="right", padx=(0, 4))
            pill.pack_propagate(False)
            self._nav_pills[page_id] = pill

        # -- Spacer ----
        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(expand=True)

        # -- Footer ----
        ctk.CTkFrame(
            self.sidebar, height=1, fg_color=T.SIDEBAR_BORDER
        ).pack(fill="x", padx=18, pady=(0, 10))

        footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer.pack(fill="x", padx=18, pady=(0, 16))

        ctk.CTkLabel(
            footer,
            text="v1.0  •  OMR QA",
            font=T.tiny(),
            text_color=T.SIDEBAR_TEXT,
            anchor="center",
        ).pack(fill="x")

    # -- Content area ----

    def _build_content(self, parent: ctk.CTkFrame) -> None:
        self.content_frame = ctk.CTkFrame(
            parent, fg_color=T.PAGE_BG, corner_radius=0
        )
        self.content_frame.pack(side="right", fill="both", expand=True)
        self.router = PageRouter(self.root, self.content_frame)

    # -- Page registration ----

    def _register_pages(self) -> None:
        self.router.register_page(
            "dashboard",
            lambda **kw: DashboardPage(
                router=self.router,
                persistence=self.persistence,
                navigate_callback=self._navigate,
                **kw,
            ),
        )
        self.router.register_page(
            "survey_form",
            lambda **kw: SurveyFormPage(
                router=self.router,
                persistence=self.persistence,
                navigate_callback=self._navigate,
                **kw,
            ),
        )
        self.router.register_page(
            "process",
            lambda **kw: ProcessPage(
                router=self.router,
                persistence=self.persistence,
                navigate_callback=self._navigate,
                vision=self.vision,
                **kw,
            ),
        )
        self.router.register_page(
            "results",
            lambda **kw: ResultsPage(
                router=self.router,
                persistence=self.persistence,
                navigate_callback=self._navigate,
                analytics=self.analytics,
                **kw,
            ),
        )
        self.router.register_page(
            "settings",
            lambda master=None, **kw: SettingsFrame(
                master or self.content_frame,
                self.config,
                back_command=lambda: self._navigate("dashboard"),
                persistence=self.persistence,
            ),
        )

    # ----
    # Navigation
    # ----

    def _navigate(self, page_id: str, **kwargs: Any) -> None:
        # Guard pages that need a survey_id
        if page_id in ("process", "results") and "survey_id" not in kwargs:
            self._navigate("dashboard")
            return

        # Update sidebar highlight + right pill
        for pid, btn in self._nav_btns.items():
            pill = self._nav_pills.get(pid)
            icon_name = next((ic for p, ic, _ in _NAV_ITEMS if p == pid), "dashboard")
            if pid == page_id:
                btn.configure(
                    image=IC.icon(icon_name, size=16, color=_NAV_ICON_COLOR_ACTIVE),
                    fg_color=T.SIDEBAR_ACTIVE_BG,
                    text_color=T.SIDEBAR_TEXT_ACTIVE,
                    font=T.font(13, "bold"),
                )
                if pill:
                    pill.configure(fg_color=T.SIDEBAR_ACTIVE_PILL)
            else:
                btn.configure(
                    image=IC.icon(icon_name, size=16, color=_NAV_ICON_COLOR),
                    fg_color="transparent",
                    text_color=T.SIDEBAR_TEXT,
                    font=T.font(13),
                )
                if pill:
                    pill.configure(fg_color="transparent")

        self.router.navigate(page_id, **kwargs)

    # ----
    # Language refresh
    # ----

    def _on_lang_change(self) -> None:
        self.root.title(_("app_title"))
        for page_id, icon_name, key in _NAV_ITEMS:
            btn = self._nav_btns.get(page_id)
            if btn:
                btn.configure(text=f"  {_(key)}")
        self._navigate("dashboard")

    # ----
    # Run
    # ----

    def run(self) -> None:
        self.root.mainloop()
