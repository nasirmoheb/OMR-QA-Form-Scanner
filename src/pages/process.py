"""Process page — image upload, thumbnail grid, and OMR scanning."""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any

import customtkinter as ctk

import icons as IC
import theme as T
from i18n import _, is_rtl, rtl_text
from models import FormResult
from persistence import PersistenceManager
from vision_processor import VisionProcessor
from .base import BasePage, PageRouter

logger = logging.getLogger("omr_qa_scanner")

# Status - (colour, i18n key)
_STATUS_MAP = {
    "Queued":     (T.TEXT_MUTED,    "queued"),
    "Processing": (T.INFO,          "processing"),
    "Success":    (T.SUCCESS,       "success"),
    "Warning":    (T.WARNING,       "warning"),
    "Error":      (T.ERROR,         "error"),
}


class ProcessPage(BasePage):
    """Per-survey image upload and OMR processing."""

    def __init__(
        self,
        router: PageRouter,
        persistence: PersistenceManager,
        survey_id: int,
        folder_path: str = "",
        vision: VisionProcessor | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(router, **kwargs)
        self.persistence = persistence
        self.survey_id = survey_id
        self.folder_path = folder_path
        self.vision = vision or VisionProcessor()

        self.image_files: list[Path] = []
        self.thumb_labels: dict[Path, ctk.CTkLabel] = {}
        self.is_scanning = False

        self._build()

        if self.folder_path and Path(self.folder_path).exists():
            self._load_folder(Path(self.folder_path))

    # RTL helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _start() -> str:
        return "right" if is_rtl() else "left"

    @staticmethod
    def _end() -> str:
        return "left" if is_rtl() else "right"

    @staticmethod
    def _anchor() -> str:
        return "e" if is_rtl() else "w"

    @staticmethod
    def _compound() -> str:
        return "right" if is_rtl() else "left"

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        self.configure(fg_color=T.PAGE_BG)

        # -- Header ----
        header = T.transparent(self)
        header.pack(fill="x", padx=T.PAGE_PADDING, pady=(T.PAGE_PADDING, 0))

        # Title
        ctk.CTkLabel(
            header, text=_("scan_process_forms"), font=T.h1(), text_color=T.TEXT_PRIMARY
        ).pack(anchor=self._anchor())

        # Subtitle
        ctk.CTkLabel(
            header, text=_("scan_process_subtitle"),
            font=T.small(), text_color=T.TEXT_SECONDARY, justify=self._start()
        ).pack(anchor=self._anchor(), pady=(4, 0))

        # -- Main Content (2 Columns) ----
        content_wrap = T.transparent(self)
        content_wrap.pack(fill="both", expand=True, padx=T.PAGE_PADDING, pady=16)

        left_col = T.transparent(content_wrap)
        left_col.pack(side=self._start(), fill="both", expand=True, padx=(0, 16) if not is_rtl() else (16, 0))

        right_col = T.transparent(content_wrap)
        right_col.pack(side=self._end(), fill="y", padx=(16, 0) if not is_rtl() else (0, 16))

        # -------------------------------------------------------------
        # LEFT COLUMN: Thumbnail Grid
        # -------------------------------------------------------------
        thumb_card = T.card(left_col)
        thumb_card.pack(fill="both", expand=True)

        thumb_header = T.transparent(thumb_card)
        thumb_header.pack(fill="x", padx=T.CARD_PADDING, pady=(T.CARD_PADDING, 0))
        ctk.CTkLabel(
            thumb_header, text="  " + _("queued_images"), image=IC.icon("image", size=18, color=T.ACCENT[1]),
            font=T.h2(), text_color=T.TEXT_PRIMARY, compound=self._compound()
        ).pack(side=self._start())

        self.count_lbl = T.muted_label(thumb_header, "")
        self.count_lbl.pack(side=self._end())

        self.thumb_frame = ctk.CTkScrollableFrame(
            thumb_card, fg_color="transparent", corner_radius=0
        )
        self.thumb_frame.pack(fill="both", expand=True, padx=T.CARD_PADDING, pady=T.CARD_PADDING)

        # -------------------------------------------------------------
        # RIGHT COLUMN: Scanning Desk
        # -------------------------------------------------------------
        
        # -- Survey Meta Details ----
        survey = None
        try:
            survey = self.persistence.get_survey(self.survey_id)
        except Exception:
            logger.warning("Could not load survey id=%s", self.survey_id)

        if survey:
            meta_card = T.card(right_col)
            meta_card.pack(fill="x", pady=(0, 16), ipadx=10)
            
            meta_inner = T.transparent(meta_card)
            meta_inner.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)
            
            ctk.CTkLabel(
                meta_inner, text=_("survey_details"),
                font=T.font(12, "bold"), text_color=T.TEXT_SECONDARY
            ).pack(anchor=self._anchor(), pady=(0, 12))

            ctk.CTkLabel(
                meta_inner, image=IC.icon("book", size=15, color=T.ACCENT[1]),
                text=f"  {survey.subject}", font=T.h4(), text_color=T.TEXT_PRIMARY,
                anchor=self._anchor(), compound=self._compound()
            ).pack(anchor=self._anchor())

            ctk.CTkLabel(
                meta_inner, text=f"{survey.professor}\n{survey.semester} • {survey.academic_year}",
                font=T.small(), text_color=T.TEXT_SECONDARY, anchor=self._anchor(), justify=self._start()
            ).pack(anchor=self._anchor(), pady=(8, 0))

        # -- Actions Card ----
        action_card = T.card(right_col)
        action_card.pack(fill="x", ipadx=10)

        action_header = T.transparent(action_card)
        action_header.pack(fill="x", padx=T.CARD_PADDING, pady=(T.CARD_PADDING, 0))
        ctk.CTkLabel(
            action_header, text=_("scan_actions"),
            font=T.font(12, "bold"), text_color=T.TEXT_SECONDARY
        ).pack(anchor=self._anchor())

        action_body = T.transparent(action_card)
        action_body.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)

        # Add Images
        IC.icon_button(
            action_body, "upload", text="  " + _("add_images"),
            size=16, color=T.TEXT_PRIMARY[1], height=44,
            fg_color="transparent", hover_color=T.SURFACE_RAISED,
            text_color=T.TEXT_PRIMARY, font=T.font(13),
            border_width=1, border_color=T.CARD_BORDER,
            command=self._on_add,
        ).pack(fill="x", pady=(0, 12))

        # Start Scanning
        self.scan_btn = ctk.CTkButton(
            action_body, text="  " + _("start_scanning"), image=IC.icon("scan", size=16, color="#000000"),
            height=44, corner_radius=T.RADIUS_MD, fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
            text_color="#000000", font=T.font(14, "bold"),
            state="disabled", command=self._on_scan,
        )
        self.scan_btn.pack(fill="x", pady=(0, 20))

        # -- Progress Bar ----
        T.divider(action_body).pack(fill="x", pady=(0, 20))
        
        self.progress_lbl = ctk.CTkLabel(
            action_body, text=_("ready_to_scan"), font=T.tiny(), text_color=T.TEXT_MUTED, anchor=self._anchor()
        )
        self.progress_lbl.pack(fill="x", pady=(0, 4))

        self.progress_bar = ctk.CTkProgressBar(
            action_body, height=8, corner_radius=T.RADIUS_SM,
            fg_color=T.CHIP_BG, progress_color=T.ACCENT,
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x")

        # Discard / Back
        ctk.CTkButton(
            action_body, text="  " + _("discard_exit"), image=IC.icon("arrow_left", size=16, color=T.TEXT_SECONDARY[1]),
            height=36, corner_radius=T.RADIUS_MD, fg_color="transparent", hover_color=T.SURFACE_RAISED,
            text_color=T.TEXT_SECONDARY, font=T.font(13), command=lambda: self.go("dashboard"),
        ).pack(fill="x", pady=(20, 0))

    # ------------------------------------------------------------------
    # Image management
    # ------------------------------------------------------------------

    def _on_add(self) -> None:
        files = filedialog.askopenfilenames(
            filetypes=[("Image files", "*.jpg *.jpeg *.png")]
        )
        for f in files:
            p = Path(f)
            if p not in self.image_files:
                self.image_files.append(p)
        self._refresh_thumbs()
        self._update_scan_btn()

    def _load_folder(self, folder: Path) -> None:
        exts = {".jpg", ".jpeg", ".png"}
        self.image_files = sorted(
            p for p in folder.iterdir()
            if p.is_file() and p.suffix.lower() in exts
        )
        self._refresh_thumbs()
        self._update_scan_btn()

    def _refresh_thumbs(self) -> None:
        for w in self.thumb_frame.winfo_children():
            w.destroy()
        self.thumb_labels.clear()

        for path in self.image_files:
            tile = T.inner_card(
                self.thumb_frame,
                width=110,
                height=90,
                corner_radius=T.RADIUS_MD,
            )
            tile.pack(side=self._start(), padx=(0, 8) if not is_rtl() else (8, 0), pady=4)
            tile.pack_propagate(False)

            name = path.name
            display = name if len(name) <= 13 else name[:13] + "…"
            ctk.CTkLabel(
                tile,
                text=display,
                font=T.tiny(),
                text_color=T.TEXT_SECONDARY,
                wraplength=100,
            ).pack(pady=(10, 2))

            status_lbl = ctk.CTkLabel(
                tile,
                text=_("queued"),
                font=T.tiny(),
                text_color=T.TEXT_MUTED,
            )
            status_lbl.pack()
            self.thumb_labels[path] = status_lbl

        self.count_lbl.configure(
            text=f"{len(self.image_files)} " + _("images_queued") if self.image_files else ""
        )

    def _update_thumb_status(self, path: Path, status: str) -> None:
        lbl = self.thumb_labels.get(path)
        if not lbl:
            return
        color, key = _STATUS_MAP.get(status, (T.TEXT_MUTED, status.lower()))
        lbl.configure(text=_(key), text_color=color)

    def _update_scan_btn(self) -> None:
        state = "normal" if self.image_files and not self.is_scanning else "disabled"
        self.scan_btn.configure(state=state)

    # ------------------------------------------------------------------
    # Scanning
    # ------------------------------------------------------------------

    def _on_scan(self) -> None:
        if self.is_scanning or not self.image_files:
            if not self.image_files:
                messagebox.showwarning(rtl_text(_("start_scanning")), rtl_text(_("no_images_queued")))
            return
        self.is_scanning = True
        self.scan_btn.configure(state="disabled")
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self) -> None:
        n = len(self.image_files)
        counts = {"success": 0, "warning": 0, "error": 0}

        for i, path in enumerate(self.image_files):
            self.after(0, lambda p=path: self._update_thumb_status(p, "Processing"))
            self.after(0, lambda t=_("scanning_image", current=i + 1, total=n):
                       self.progress_lbl.configure(text=t))
            self.after(0, lambda v=(i + 1) / n: self.progress_bar.set(v))

            try:
                result = self.vision.process_form(path)
            except Exception:
                logger.exception("Error processing %s", path)
                result = {
                    "status": "error", "form_confidence": 0.0,
                    "Form_ID": path.stem, "Form_Score": 0.0, "Valid": False,
                }
                for qi in range(1, 15):
                    result[f"Q{qi}"] = "Invalid"

            if result.get("status") != "ok":
                status = "Error";  counts["error"] += 1
            elif result.get("form_confidence", 0.0) < 0.5:
                status = "Warning"; counts["warning"] += 1
            else:
                status = "Success"; counts["success"] += 1

            try:
                self.persistence.create_form_result(self._to_form_result(result, path))
            except Exception:
                logger.exception("Failed to save result for %s", path)

            self.after(0, lambda p=path, s=status: self._update_thumb_status(p, s))

        # Mark survey as Processed
        try:
            survey = self.persistence.get_survey(self.survey_id)
            if survey:
                survey.status = "Processed"
                survey.updated_at = datetime.now().isoformat()
                self.persistence.update_survey(survey)
        except Exception:
            logger.exception("Failed to update survey status")

        self.after(0, lambda: self.progress_lbl.configure(text=_("scan_complete")))
        self.after(0, lambda: setattr(self, "is_scanning", False))
        self.after(0, self._update_scan_btn)

        summary = (
            f"{_('scan_summary')}\n"
            f"{_('forms_success')}: {counts['success']}\n"
            f"{_('forms_warning')}: {counts['warning']}\n"
            f"{_('forms_error')}: {counts['error']}"
        )
        self.after(0, lambda: messagebox.showinfo(rtl_text(_("scan_complete")), rtl_text(summary)))

    def _to_form_result(self, result: dict[str, Any], path: Path) -> FormResult:
        return FormResult(
            survey_id=self.survey_id,
            form_id=result.get("Form_ID", path.stem),
            image_path=str(path),
            q1=result.get("Q1", ""), q2=result.get("Q2", ""),
            q3=result.get("Q3", ""), q4=result.get("Q4", ""),
            q5=result.get("Q5", ""), q6=result.get("Q6", ""),
            q7=result.get("Q7", ""), q8=result.get("Q8", ""),
            q9=result.get("Q9", ""), q10=result.get("Q10", ""),
            q11=result.get("Q11", ""), q12=result.get("Q12", ""),
            q13=result.get("Q13", ""), q14=result.get("Q14", ""),
            form_score=result.get("Form_Score", 0.0),
            valid=result.get("Valid", False),
            confidence=result.get("form_confidence", 0.0),
            manually_corrected=False,
        )
