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
from i18n import _
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

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        self.configure(fg_color=T.PAGE_BG)

        # -- Header ----
        header = T.transparent(self)
        header.pack(fill="x", padx=T.PAGE_PADDING, pady=(T.PAGE_PADDING, 0))

        IC.icon_button(
            header, "arrow_left", text="  " + _("back"),
            size=14, color=T._D_TEXT2, width=110, height=36,
            fg_color=T.GHOST_BG, hover_color=T.GHOST_HOVER,
            text_color=T.GHOST_TEXT, border_width=1, border_color=T.GHOST_BORDER,
            font=T.body(), command=lambda: self.go("dashboard"),
        ).pack(side="left")

        T.page_title(header, _("process")).pack(side="left", padx=16)

        # -- Survey meta card ----
        survey = None
        try:
            survey = self.persistence.get_survey(self.survey_id)
        except Exception:
            logger.warning("Could not load survey id=%s", self.survey_id)

        if survey:
            meta = T.card(self)
            meta.pack(fill="x", padx=T.PAGE_PADDING, pady=(16, 0))

            meta_inner = T.transparent(meta)
            meta_inner.pack(fill="x", padx=T.CARD_PADDING, pady=14)

            ctk.CTkLabel(
                meta_inner,
                image=IC.icon("book", size=15, color=T._D_TEXT1),
                text=f"  {survey.subject}",
                font=T.h4(), text_color=T.TEXT_PRIMARY, anchor="w",
                compound="left",
            ).pack(anchor="w")

            ctk.CTkLabel(
                meta_inner,
                image=IC.icon("user", size=12, color=T._D_TEXT2),
                text=f"  {survey.professor}   •   {survey.semester}   •   {survey.academic_year}",
                font=T.small(), text_color=T.TEXT_SECONDARY, anchor="w",
                compound="left",
            ).pack(anchor="w", pady=(4, 0))

        # -- Upload zone ----
        upload_card = T.card(self)
        upload_card.pack(fill="x", padx=T.PAGE_PADDING, pady=(16, 0))

        upload_inner = T.transparent(upload_card)
        upload_inner.pack(fill="x", padx=T.CARD_PADDING, pady=14)

        T.section_title(upload_inner, _("add_images")).pack(anchor="w", pady=(0, 10))

        btn_row = T.transparent(upload_inner)
        btn_row.pack(fill="x")

        IC.icon_button(
            btn_row, "upload", text="  " + _("add_images"),
            size=15, color="#FFFFFF", width=160,
            fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
            text_color="#FFFFFF", font=T.font(13, "bold"),
            corner_radius=T.RADIUS_MD,
            command=self._on_add,
        ).pack(side="left")

        self.folder_lbl = T.muted_label(
            btn_row,
            self.folder_path or _("no_folder"),
        )
        self.folder_lbl.pack(side="left", padx=12)

        # -- Thumbnail grid ----
        thumb_card = T.card(self)
        thumb_card.pack(fill="x", padx=T.PAGE_PADDING, pady=(12, 0))

        self.thumb_frame = ctk.CTkScrollableFrame(
            thumb_card,
            fg_color="transparent",
            height=160,
            corner_radius=0,
        )
        self.thumb_frame.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)

        # -- Progress ----
        prog_card = T.card(self)
        prog_card.pack(fill="x", padx=T.PAGE_PADDING, pady=(12, 0))

        prog_inner = T.transparent(prog_card)
        prog_inner.pack(fill="x", padx=T.CARD_PADDING, pady=14)

        self.progress_lbl = ctk.CTkLabel(
            prog_inner,
            text="",
            font=T.body(),
            text_color=T.TEXT_SECONDARY,
            anchor="w",
        )
        self.progress_lbl.pack(fill="x", pady=(0, 8))

        self.progress_bar = ctk.CTkProgressBar(
            prog_inner,
            height=10,
            corner_radius=T.RADIUS_SM,
            fg_color=T.CHIP_BG,
            progress_color=T.ACCENT,
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x")

        # -- Scan button ----
        action_row = T.transparent(self)
        action_row.pack(fill="x", padx=T.PAGE_PADDING, pady=(16, T.PAGE_PADDING))

        self.scan_btn = IC.icon_button(
            action_row, "scan", text="  " + _("start_scanning"),
            size=16, color="#FFFFFF",
            state="disabled", width=200, height=44,
            fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
            text_color="#FFFFFF", font=T.font(13, "bold"),
            corner_radius=T.RADIUS_MD,
            command=self._on_scan,
        )
        self.scan_btn.pack(side="left")

        self.count_lbl = T.muted_label(action_row, "")
        self.count_lbl.pack(side="left", padx=16)

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
            tile.pack(side="left", padx=(0, 8), pady=4)
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
            text=f"{len(self.image_files)} image(s) queued" if self.image_files else ""
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
                messagebox.showwarning(_("start_scanning"), _("no_images_queued"))
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
        self.after(0, lambda: messagebox.showinfo(_("scan_complete"), summary))

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
