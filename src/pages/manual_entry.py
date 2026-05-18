"""Manual entry page — enter response counts manually for each question."""

from __future__ import annotations

import logging
from datetime import datetime
from tkinter import messagebox
from typing import Any

import customtkinter as ctk

import icons as IC
import theme as T
from i18n import _, is_rtl, rtl_text
from models import FormResult, Survey
from persistence import PersistenceManager
from analytics_engine import AnalyticsEngine
from .base import BasePage, PageRouter
from config import Config
from report_generator import to_persian_num

logger = logging.getLogger("tadris_qa_system")


class ManualEntryPage(BasePage):
    """Page for manually entering counts of Yes, Somewhat, No answers for a survey."""

    def __init__(
        self,
        router: PageRouter,
        persistence: PersistenceManager,
        survey_id: int,
        analytics: AnalyticsEngine | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(router, **kwargs)
        self.persistence = persistence
        self.survey_id = survey_id
        self.analytics = analytics or AnalyticsEngine()
        self.config = Config.from_persistence(self.persistence)

        self.survey: Survey | None = self.persistence.get_survey(survey_id)
        self.question_texts: list[str] | None = self.persistence.get_setting("question_texts", None)

        # Default fallback questions if not customized
        self._default_questions = [
            "آیا در آغاز سمستر کورس پالیسی تشریح گردیده است؟",
            "آیا تدریس مطابق کورس پالیسی صورت گرفته است؟",
            "آیا مواد درسی برای شما معرفی شده و موجود است؟",
            "آیا تدریس استاد قابل فهم است؟",
            "آیا از میتود تدریس استاد راضی هستید؟",
            "آیا استاد محصلان را در تدریس سهم میسازد؟",
            "آیا از سلوک و رویه اکادمیک استاد راضی هستید؟",
            "آیا استاد با پلان درسی منظم داخل صنف میشود؟",
            "آیا استاد به سوالات شما جواب قناعتبخش میدهد؟",
            "آیا استاد پابند به اصول، وقت و زمان معین میباشد؟",
            "(معکوس) آیا استاد به موضوعات غیرمرتبط تماس میگیرد؟",
            "آیا مشکلات درسی شما توسط استاد حل میگردد؟",
            "آیا از شیوههای ارزیابی استاد راضی هستید؟",
            "آیا استاد از تکنالوژی معلوماتی استفاده مینماید؟",
        ]

        # References to entry fields
        self.entries_yes: list[ctk.CTkEntry] = []
        self.entries_somewhat: list[ctk.CTkEntry] = []
        self.entries_no: list[ctk.CTkEntry] = []

        self._build()

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
            header, text=_("manual_data_entry"), font=T.h1(), text_color=T.TEXT_PRIMARY
        ).pack(anchor=self._anchor())

        # Subtitle
        ctk.CTkLabel(
            header, text=(_("survey_details") if not is_rtl() else "جزئیات نظرسنجی"),
            font=T.small(), text_color=T.TEXT_SECONDARY, justify=self._start()
        ).pack(anchor=self._anchor(), pady=(4, 0))

        # -- Main Container (Form & Sidebar Actions) ----
        content_wrap = T.transparent(self)
        content_wrap.pack(fill="both", expand=True, padx=T.PAGE_PADDING, pady=16)

        left_col = T.transparent(content_wrap)
        left_col.pack(side=self._start(), fill="both", expand=True, padx=(0, 16) if not is_rtl() else (16, 0))

        right_col = T.transparent(content_wrap)
        right_col.pack(side=self._end(), fill="y", padx=(16, 0) if not is_rtl() else (0, 16))

        # -------------------------------------------------------------
        # LEFT COLUMN: Question Entry List
        # -------------------------------------------------------------
        scroll_card = T.card(left_col)
        scroll_card.pack(fill="both", expand=True)

        self.form_scroll = ctk.CTkScrollableFrame(
            scroll_card, fg_color="transparent", corner_radius=0
        )
        self.form_scroll.pack(fill="both", expand=True, padx=T.CARD_PADDING, pady=T.CARD_PADDING)

        # Table Header Row (Column Labels)
        tbl_hdr = T.transparent(self.form_scroll)
        tbl_hdr.pack(fill="x", pady=(0, 12))

        # Get configured score weights
        score_yes = self.config.SCORE_YES
        score_somewhat = self.config.SCORE_SOMEWHAT
        score_no = self.config.SCORE_NO

        s_yes = to_persian_num(score_yes) if is_rtl() else str(score_yes)
        s_sw = to_persian_num(score_somewhat) if is_rtl() else str(score_somewhat)
        s_no = to_persian_num(score_no) if is_rtl() else str(score_no)

        label_yes = f"{_('count_yes')} ({s_yes})"
        label_sw = f"{_('count_somewhat')} ({s_sw})"
        label_no = f"{_('count_no')} ({s_no})"

        # Column structure: Question Text | Yes | Somewhat | No
        # We pack the elements based on layout direction (RTL or LTR)
        hdr_lbl_q = ctk.CTkLabel(
            tbl_hdr, text=_("question"), font=T.font(12, "bold"), text_color=T.TEXT_SECONDARY, anchor=self._anchor()
        )
        hdr_lbl_q.pack(side=self._start(), fill="x", expand=True, padx=(10, 10))

        hdr_lbl_no = ctk.CTkLabel(
            tbl_hdr, text=label_no, font=T.font(12, "bold"), text_color=T.TEXT_SECONDARY, width=80
        )
        hdr_lbl_no.pack(side=self._end(), padx=(5, 12) if not is_rtl() else (12, 5))

        hdr_lbl_sw = ctk.CTkLabel(
            tbl_hdr, text=label_sw, font=T.font(12, "bold"), text_color=T.TEXT_SECONDARY, width=80
        )
        hdr_lbl_sw.pack(side=self._end(), padx=5)

        hdr_lbl_yes = ctk.CTkLabel(
            tbl_hdr, text=label_yes, font=T.font(12, "bold"), text_color=T.TEXT_SECONDARY, width=80
        )
        hdr_lbl_yes.pack(side=self._end(), padx=5)

        # Fetch existing results if present to prefill counts
        results = self.persistence.get_form_results(self.survey_id)

        # Build entry row for each of the 14 questions
        for i in range(14):
            q_num = i + 1
            
            # Fetch question text
            if self.question_texts and len(self.question_texts) == 14:
                q_text = self.question_texts[i]
            else:
                q_text = self._default_questions[i]

            # Format the text with Q number
            display_text = f"{q_num}. {q_text}"

            row_frame = T.inner_card(self.form_scroll, corner_radius=T.RADIUS_MD)
            row_frame.pack(fill="x", pady=4)

            # Question Text label
            lbl_q = ctk.CTkLabel(
                row_frame, text=display_text, font=T.body(), text_color=T.TEXT_PRIMARY,
                anchor=self._anchor(), justify=self._start(), wraplength=600
            )
            lbl_q.pack(side=self._start(), fill="both", expand=True, padx=12, pady=8)

            # Calculate counts if results exist
            existing_yes = 0
            existing_somewhat = 0
            existing_no = 0

            if results:
                for fr in results:
                    answers = fr.answers()
                    if i < len(answers):
                        ans = answers[i]
                        if ans == "Yes":
                            existing_yes += 1
                        elif ans == "Somewhat":
                            existing_somewhat += 1
                        elif ans == "No":
                            existing_no += 1

            # Entries for choice counts
            ent_no = ctk.CTkEntry(
                row_frame, width=64, height=32, corner_radius=T.RADIUS_SM,
                fg_color=T.INPUT_BG, border_color=T.INPUT_BORDER, text_color=T.TEXT_PRIMARY,
                font=T.body(), justify="center", placeholder_text="0"
            )
            ent_no.pack(side=self._end(), padx=(5, 12) if not is_rtl() else (12, 5), pady=8)
            if results:
                ent_no.insert(0, str(existing_no))
            self.entries_no.append(ent_no)

            ent_sw = ctk.CTkEntry(
                row_frame, width=64, height=32, corner_radius=T.RADIUS_SM,
                fg_color=T.INPUT_BG, border_color=T.INPUT_BORDER, text_color=T.TEXT_PRIMARY,
                font=T.body(), justify="center", placeholder_text="0"
            )
            ent_sw.pack(side=self._end(), padx=5, pady=8)
            if results:
                ent_sw.insert(0, str(existing_somewhat))
            self.entries_somewhat.append(ent_sw)

            ent_yes = ctk.CTkEntry(
                row_frame, width=64, height=32, corner_radius=T.RADIUS_SM,
                fg_color=T.INPUT_BG, border_color=T.INPUT_BORDER, text_color=T.TEXT_PRIMARY,
                font=T.body(), justify="center", placeholder_text="0"
            )
            ent_yes.pack(side=self._end(), padx=5, pady=8)
            if results:
                ent_yes.insert(0, str(existing_yes))
            self.entries_yes.append(ent_yes)

            # Restrict inputs to numbers only
            def _validate_numeric(char: str) -> bool:
                return char.isdigit() or char == ""
            
            vc = row_frame.register(_validate_numeric)
            ent_yes.configure(validate="key", validatecommand=(vc, "%S"))
            ent_sw.configure(validate="key", validatecommand=(vc, "%S"))
            ent_no.configure(validate="key", validatecommand=(vc, "%S"))

        # -------------------------------------------------------------
        # RIGHT COLUMN: Actions and Survey Metadata
        # -------------------------------------------------------------
        if self.survey:
            meta_card = T.card(right_col)
            meta_card.pack(fill="x", pady=(0, 16), ipadx=10)

            meta_inner = T.transparent(meta_card)
            meta_inner.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)

            ctk.CTkLabel(
                meta_inner, text=(_("survey_details") if not is_rtl() else "جزئیات نظرسنجی"),
                font=T.font(12, "bold"), text_color=T.TEXT_SECONDARY
            ).pack(anchor=self._anchor(), pady=(0, 12))

            ctk.CTkLabel(
                meta_inner, image=IC.icon("book", size=15, color=T.ACCENT[1]),
                text=f"  {self.survey.subject}", font=T.h4(), text_color=T.TEXT_PRIMARY,
                anchor=self._anchor(), compound=self._compound()
            ).pack(anchor=self._anchor())

            ctk.CTkLabel(
                meta_inner, text=f"{self.survey.professor}\n{self.survey.semester} • {self.survey.academic_year}",
                font=T.small(), text_color=T.TEXT_SECONDARY, anchor=self._anchor(), justify=self._start()
            ).pack(anchor=self._anchor(), pady=(8, 0))

            # Score Weights (Yes: 100, Somewhat: 50, No: 0)
            score_title = "نمره‌دهی مقیاس" if is_rtl() else "Scoring Scale"
            ctk.CTkLabel(
                meta_inner, text=score_title,
                font=T.font(11, "bold"), text_color=T.TEXT_SECONDARY
            ).pack(anchor=self._anchor(), pady=(16, 4))

            weights_text = (
                f"بلی: {s_yes} • نسبتاً: {s_sw} • نخیر: {s_no}" if is_rtl() else
                f"Yes: {s_yes} • Somewhat: {s_sw} • No: {s_no}"
            )
            ctk.CTkLabel(
                meta_inner, text=weights_text, font=T.small(), text_color=T.TEXT_SECONDARY,
                anchor=self._anchor(), justify=self._start()
            ).pack(anchor=self._anchor())

        # Actions Card
        action_card = T.card(right_col)
        action_card.pack(fill="x", ipadx=10)

        action_header = T.transparent(action_card)
        action_header.pack(fill="x", padx=T.CARD_PADDING, pady=(T.CARD_PADDING, 0))
        ctk.CTkLabel(
            action_header, text=(_("scan_actions") if not is_rtl() else "عملیات‌ها"),
            font=T.font(12, "bold"), text_color=T.TEXT_SECONDARY
        ).pack(anchor=self._anchor())

        action_body = T.transparent(action_card)
        action_body.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)

        # Save Button
        self.save_btn = ctk.CTkButton(
            action_body, text="  " + (_("save_results") if not is_rtl() else "ذخیره نتایج"),
            image=IC.icon("save", size=16, color="#000000"),
            height=44, corner_radius=T.RADIUS_MD, fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
            text_color="#000000", font=T.font(14, "bold"),
            command=self._on_save
        )
        self.save_btn.pack(fill="x", pady=(0, 12))

        # Discard / Back Button
        ctk.CTkButton(
            action_body, text="  " + _("cancel"), image=IC.icon("arrow_left", size=16, color=T.TEXT_SECONDARY[1]),
            height=36, corner_radius=T.RADIUS_MD, fg_color="transparent", hover_color=T.SURFACE_RAISED,
            text_color=T.TEXT_SECONDARY, font=T.font(13), command=lambda: self.go("dashboard")
        ).pack(fill="x")

    # ------------------------------------------------------------------
    # Action Handlers
    # ------------------------------------------------------------------

    def _on_save(self) -> None:
        """Validate, generate synthetic FormResults, and save to the database."""
        # 1. Gather & Validate Counts
        yes_counts: list[int] = []
        somewhat_counts: list[int] = []
        no_counts: list[int] = []

        try:
            for i in range(14):
                val_yes = self.entries_yes[i].get().strip()
                val_sw = self.entries_somewhat[i].get().strip()
                val_no = self.entries_no[i].get().strip()

                yes_counts.append(int(val_yes) if val_yes else 0)
                somewhat_counts.append(int(val_sw) if val_sw else 0)
                no_counts.append(int(val_no) if val_no else 0)
        except ValueError:
            messagebox.showerror(
                rtl_text(_("error")),
                rtl_text(_("invalid_number") if "invalid_number" in _TRANSLATIONS.get(T.LANGUAGE, {}) else "Please enter valid numbers.")
            )
            return

        # Check if at least one entry has a count > 0
        total_entered = sum(yes_counts) + sum(somewhat_counts) + sum(no_counts)
        if total_entered == 0:
            messagebox.showwarning(
                rtl_text(_("warning")),
                rtl_text("Please enter at least one response count." if not is_rtl() else "لطفاً حداقل تعداد یک پاسخ را وارد کنید.")
            )
            return

        # 2. Determine N (max total forms)
        # N will be the maximum total responses across all 14 questions
        totals_per_q = [
            yes_counts[i] + somewhat_counts[i] + no_counts[i]
            for i in range(14)
        ]
        N = max(totals_per_q)

        if N == 0:
            return

        # 3. Confirm Save
        confirm_msg = (
            f"Are you sure you want to save? This will generate {N} form results and overwrite any existing data for this survey."
            if not is_rtl() else
            f"آیا از ذخیره نتایج مطمئن هستید؟ این عملیات {N} پاسخ‌نامه تولید کرده و داده‌های قبلی این نظرسنجی را پاک می‌کند."
        )
        if not messagebox.askyesno(rtl_text(_("save")), rtl_text(confirm_msg)):
            return

        # Disable save button to prevent double-clicks
        self.save_btn.configure(state="disabled")
        self.update()

        try:
            # 4. Clear existing form results
            self.persistence.delete_form_results_for_survey(self.survey_id)

            # 5. Build Pools of Answers & Generate Synthetic FormResults
            # For each question, we construct a list of size N containing Yes, Somewhat, No, and padded with Invalid
            pools: list[list[str]] = []
            for i in range(14):
                pool = (
                    ["Yes"] * yes_counts[i] +
                    ["Somewhat"] * somewhat_counts[i] +
                    ["No"] * no_counts[i]
                )
                # Pad to size N with "Invalid"
                pool += ["Invalid"] * (N - len(pool))
                pools.append(pool)

            # Generate N synthetic FormResult records
            for j in range(N):
                answers = [pools[i][j] for i in range(14)]
                form_score = self.analytics.calculate_form_score(answers)

                # Form is valid if it contains at least one non-Invalid answer
                valid = any(ans != "Invalid" for ans in answers)

                result = FormResult(
                    survey_id=self.survey_id,
                    form_id=f"Manual_Form_{j + 1}",
                    image_path="",  # No image for manual entries
                    q1=answers[0], q2=answers[1], q3=answers[2], q4=answers[3],
                    q5=answers[4], q6=answers[5], q7=answers[6], q8=answers[7],
                    q9=answers[8], q10=answers[9], q11=answers[10], q12=answers[11],
                    q13=answers[12], q14=answers[13],
                    form_score=form_score,
                    valid=valid,
                    confidence=1.0,  # 100% confidence for manual entry
                    manually_corrected=True,
                    comment="Manually Entered Data"
                )
                self.persistence.create_form_result(result)

            # 6. Mark survey as Processed
            if self.survey:
                self.survey.status = "Processed"
                self.survey.updated_at = datetime.now().isoformat()
                self.persistence.update_survey(self.survey)

            # Show Success Summary
            success_msg = (
                f"Successfully saved manually entered data.\nGenerated {N} synthetic form results."
                if not is_rtl() else
                f"اطلاعات ثبت‌شده با موفقیت ذخیره شد.\nتعداد {N} پاسخ‌نامه به صورت خودکار تولید شد."
            )
            messagebox.showinfo(rtl_text(_("scan_complete")), rtl_text(success_msg))

            # Navigate back to dashboard and trigger results open
            self.go("dashboard", _open_report=self.survey_id)

        except Exception as exc:
            logger.exception("Manual data entry save failed")
            messagebox.showerror(rtl_text(_("error")), rtl_text(f"Failed to save manual data:\n{exc}"))
            self.save_btn.configure(state="normal")
