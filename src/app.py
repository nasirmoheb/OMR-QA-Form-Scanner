"""Main application window — sidebar navigation + page routing."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import customtkinter as ctk

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


class OMRGUI:
    """Root application window with a fixed sidebar and dynamic content area."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()

        ctk.set_appearance_mode(self.config.APPEARANCE_MODE)
        I18n.set_language(self.config.LANGUAGE)

        self.persistence = PersistenceManager()
        self.vision      = VisionProcessor(config=self.config)
        self.analytics   = AnalyticsEngine(config=self.config)

        # ── Root window ────────────────────────────────────────────────
        self.root = ctk.CTk()
        self.root.title(_("app_title"))
        self.root.geometry("1280x760")
        self.root.minsize(1024, 640)

        self._build()
        I18n.register_listener(self._on_lang_change)

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        container = ctk.CTkFrame(self.root, fg_color="transparent")
        container.pack(fill="both", expand=True)

        self._build_sidebar(container)
        self._build_content(container)
        self._register_pages()
        self._navigate("dashboard")

    def _build_sidebar(self, parent: ctk.CTkFrame) -> None:
        """Fixed-width dark sidebar with logo, nav, and footer."""
        self.sidebar = ctk.CTkFrame(
            parent,
            width=T.SIDEBAR_WIDTH,
            corner_radius=0,
            fg_color=T.SIDEBAR_BG,
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # ── Logo / branding ────────────────────────────────────────────
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=20, pady=(28, 0))

        # Icon circle
        icon_bg = ctk.CTkFrame(
            logo_frame,
            width=40, height=40,
            corner_radius=10,
            fg_color=T.ACCENT,
        )
        icon_bg.pack(side="left")
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(
            icon_bg,
            text="◉",
            font=T.font(18, "bold"),
            text_color="#FFFFFF",
        ).place(relx=0.5, rely=0.5, anchor="center")

        title_col = ctk.CTkFrame(logo_frame, fg_color="transparent")
        title_col.pack(side="left", padx=(10, 0))
        ctk.CTkLabel(
            title_col,
            text="OMR Scanner",
            font=T.font(15, "bold"),
            text_color="#FFFFFF",
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_col,
            text="QA Form System",
            font=T.tiny(),
            text_color=T.SIDEBAR_TEXT,
        ).pack(anchor="w")

        # ── Divider ────────────────────────────────────────────────────
        ctk.CTkFrame(
            self.sidebar, height=1, fg_color=T.SIDEBAR_BORDER
        ).pack(fill="x", padx=20, pady=(20, 16))

        # ── Nav items ──────────────────────────────────────────────────
        self._nav_btns: dict[str, ctk.CTkButton] = {}
        nav_items = [
            ("dashboard",   "📊", _("dashboard")),
            ("survey_form", "＋", _("new_survey")),
            ("process",     "🔍", _("process")),
            ("results",     "📈", _("results")),
            ("settings",    "⚙️", _("settings")),
        ]

        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", padx=12)

        for page_id, icon, label in nav_items:
            btn = ctk.CTkButton(
                nav_frame,
                text=f"  {icon}   {label}",
                font=T.font(13),
                height=44,
                corner_radius=T.RADIUS_MD,
                fg_color="transparent",
                hover_color=T.SIDEBAR_HOVER_BG,
                text_color=T.SIDEBAR_TEXT,
                anchor="w",
                command=lambda pid=page_id: self._navigate(pid),
            )
            btn.pack(fill="x", pady=(0, 4))
            self._nav_btns[page_id] = btn

        # ── Spacer ─────────────────────────────────────────────────────
        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(expand=True)

        # ── Footer ─────────────────────────────────────────────────────
        ctk.CTkFrame(
            self.sidebar, height=1, fg_color=T.SIDEBAR_BORDER
        ).pack(fill="x", padx=20, pady=(0, 12))

        footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(
            footer,
            text="v1.0  •  OMR QA",
            font=T.tiny(),
            text_color=T.SIDEBAR_TEXT,
        ).pack(anchor="w")

    def _build_content(self, parent: ctk.CTkFrame) -> None:
        self.content_frame = ctk.CTkFrame(parent, fg_color=T.PAGE_BG, corner_radius=0)
        self.content_frame.pack(side="right", fill="both", expand=True)
        self.router = PageRouter(self.root, self.content_frame)

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

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _navigate(self, page_id: str, **kwargs: Any) -> None:
        # Guard pages that need a survey_id
        if page_id in ("process", "results") and "survey_id" not in kwargs:
            self._navigate("dashboard")
            return

        # Update sidebar highlight
        for pid, btn in self._nav_btns.items():
            if pid == page_id:
                btn.configure(
                    fg_color=T.SIDEBAR_ACTIVE_BG,
                    text_color=T.SIDEBAR_TEXT_ACTIVE,
                    font=T.font(13, "bold"),
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=T.SIDEBAR_TEXT,
                    font=T.font(13),
                )

        self.router.navigate(page_id, **kwargs)

    # ------------------------------------------------------------------
    # Language refresh
    # ------------------------------------------------------------------

    def _on_lang_change(self) -> None:
        self.root.title(_("app_title"))
        nav_labels = {
            "dashboard":   _("dashboard"),
            "survey_form": _("new_survey"),
            "process":     _("process"),
            "results":     _("results"),
            "settings":    _("settings"),
        }
        nav_icons = {
            "dashboard": "📊", "survey_form": "＋",
            "process": "🔍", "results": "📈", "settings": "⚙️",
        }
        for pid, btn in self._nav_btns.items():
            icon  = nav_icons.get(pid, "")
            label = nav_labels.get(pid, pid)
            btn.configure(text=f"  {icon}   {label}")
        self._navigate("dashboard")

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self) -> None:
        self.root.mainloop()
