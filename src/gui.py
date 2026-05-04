"""GUI layer: CustomTkinter desktop interface for the OMR scanner."""

from __future__ import annotations

import os
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog
from typing import Any

import customtkinter as ctk

from analytics_engine import AnalyticsEngine
from config import Config, setup_logging
from data_store import DataStore
from i18n import I18n, _
from settings_page import SettingsFrame
from vision_processor import VisionProcessor

logger = setup_logging()


class OMRGUI:
    """Main application window using CustomTkinter."""

    def __init__(self, config: Config | None = None) -> None:
        """Initialize the GUI.

        Args:
            config: Application configuration. Uses global defaults when
                ``None``.
        """
        self.config = config or Config()
        self.input_folder: Path | None = None
        self.image_files: list[Path] = []

        # Apply persisted preferences
        ctk.set_appearance_mode(self.config.APPEARANCE_MODE)
        I18n.set_language(self.config.LANGUAGE)

        # Core components
        self.vision = VisionProcessor(config=self.config)
        self.analytics = AnalyticsEngine(config=self.config)

        # --- Main window ------------------------------------------------ #
        self.root = ctk.CTk()
        self.root.title(_("app_title"))
        self.root.geometry("800x600")
        self.root.minsize(700, 500)

        self._create_widgets()

        # Re-translate when language changes
        I18n.register_listener(self._refresh_texts)

    # ------------------------------------------------------------------ #
    #  Widget creation
    # ------------------------------------------------------------------ #

    def _create_widgets(self) -> None:
        """Build all UI elements."""
        # Header + settings row
        self.header_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.header_frame.pack(pady=(16, 8), padx=20, fill="x")

        self.header = ctk.CTkLabel(
            self.header_frame,
            text=_("app_title"),
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        self.header.pack(side="left")

        self.settings_btn = ctk.CTkButton(
            self.header_frame,
            text=_("settings"),
            command=self.open_settings,
            width=100,
            font=ctk.CTkFont(size=12),
        )
        self.settings_btn.pack(side="right")

        # Content area that swaps between main and settings
        self.content_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.content_frame.pack(padx=0, pady=0, fill="both", expand=True)

        # --- Main view ---------------------------------------------------- #
        self.main_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True)

        # Folder selection frame
        self.folder_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.folder_frame.pack(padx=20, pady=10, fill="x")

        self.folder_label = ctk.CTkLabel(
            self.folder_frame,
            text=_("no_folder"),
            font=ctk.CTkFont(size=12),
            wraplength=600,
        )
        self.folder_label.pack(side="left", padx=12, pady=12)

        self.browse_btn = ctk.CTkButton(
            self.folder_frame,
            text=_("browse"),
            command=self.select_input_folder,
            width=100,
        )
        self.browse_btn.pack(side="right", padx=12, pady=12)

        # Image count label
        self.count_label = ctk.CTkLabel(
            self.main_frame,
            text=_("images_found", count=0),
            font=ctk.CTkFont(size=12),
        )
        self.count_label.pack(pady=5)

        # Action buttons
        self.btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.btn_frame.pack(padx=20, pady=10, fill="x")

        self.start_btn = ctk.CTkButton(
            self.btn_frame,
            text=_("start_processing"),
            command=self.start_processing,
            state="disabled",
            width=150,
        )
        self.start_btn.pack(side="left", padx=10, pady=10)

        self.report_btn = ctk.CTkButton(
            self.btn_frame,
            text=_("view_report"),
            command=self.view_report,
            state="disabled",
            width=150,
        )
        self.report_btn.pack(side="right", padx=10, pady=10)

        # Status / progress area
        self.status_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.status_frame.pack(padx=20, pady=10, fill="both", expand=True)

        self.status_text = ctk.CTkTextbox(
            self.status_frame,
            wrap="word",
            font=ctk.CTkFont(size=12),
        )
        self.status_text.pack(padx=10, pady=10, fill="both", expand=True)
        self.status_text.insert("0.0", _("welcome") + "\n")
        self.status_text.configure(state="disabled")

        # --- Settings view (initially hidden) ---------------------------- #
        self.settings_frame = SettingsFrame(
            self.content_frame,
            self.config,
            back_command=self._show_main,
        )

    # ------------------------------------------------------------------ #
    #  View toggling
    # ------------------------------------------------------------------ #

    def open_settings(self) -> None:
        """Swap to the settings page."""
        self.main_frame.pack_forget()
        self.settings_frame.pack(fill="both", expand=True)
        self.settings_btn.configure(text=_("close"), command=self._show_main)

    def _show_main(self) -> None:
        """Return to the main page."""
        self.settings_frame.pack_forget()
        self.main_frame.pack(fill="both", expand=True)
        self.settings_btn.configure(text=_("settings"), command=self.open_settings)

    def _refresh_texts(self) -> None:
        """Re-apply translations to all static widgets."""
        self.root.title(_("app_title"))
        self.header.configure(text=_("app_title"))
        self.settings_btn.configure(text=_("settings"))
        self.browse_btn.configure(text=_("browse"))
        self.start_btn.configure(text=_("start_processing"))
        self.report_btn.configure(text=_("view_report"))
        if self.input_folder is None:
            self.folder_label.configure(text=_("no_folder"))
        count = len(self.image_files)
        self.count_label.configure(text=_("images_found", count=count))

    def select_input_folder(self) -> None:
        """Open a folder dialog and validate the selection."""
        folder = filedialog.askdirectory(title=_("select_folder"))
        if not folder:
            return

        path = Path(folder)
        if not path.exists() or not path.is_dir():
            self.update_status("Error: Selected path is not a valid folder.")
            return

        self.input_folder = path
        self.folder_label.configure(text=str(path))
        self.update_status(f"Selected folder: {path}")
        self.scan_input_folder()

    # ------------------------------------------------------------------ #
    #  Folder scanning
    # ------------------------------------------------------------------ #

    def scan_input_folder(self) -> None:
        """Scan the selected folder for supported image files."""
        if self.input_folder is None:
            return

        self.image_files = [
            p
            for ext in self.config.SUPPORTED_EXTENSIONS
            for p in self.input_folder.glob(f"*{ext}")
            if p.is_file()
        ]
        self.image_files.sort()

        count = len(self.image_files)
        self.count_label.configure(text=_("images_found", count=count))
        self.update_status(f"Found {count} image(s) in {self.input_folder.name}")

        if count > 0:
            self.start_btn.configure(state="normal")
        else:
            self.start_btn.configure(state="disabled")
            self.update_status(_("no_supported"))

        # Reset report button
        self.report_btn.configure(state="disabled")

    # ------------------------------------------------------------------ #
    #  Processing
    # ------------------------------------------------------------------ #

    def start_processing(self) -> None:
        """Process all image files in the selected folder."""
        if not self.image_files:
            self.update_status(_("no_images"))
            return

        DataStore.reset()
        total = len(self.image_files)
        success = 0
        failed = 0

        self.update_status(f"Starting batch processing of {total} image(s)...\n")
        self.start_btn.configure(state="disabled")
        self.report_btn.configure(state="disabled")
        self.root.update_idletasks()

        for idx, img_path in enumerate(self.image_files, start=1):
            self.update_status(f"[{idx}/{total}] { _('processing') } {img_path.name} ...")
            self.root.update_idletasks()

            result = self.vision.process_form(img_path)

            if result["status"] == "ok":
                success += 1
            else:
                failed += 1
                self.update_status(
                    f"    ⚠ Failed: {result['status']}"
                )

            DataStore.add_form_result(result)

        batch_score = self.analytics.calculate_batch_score()
        summary = (
            f"\n{'='*40}\n"
            f"{_('batch_complete')}\n"
            f"  {_('total_images')} : {total}\n"
            f"  {_('successful')}   : {success}\n"
            f"  {_('failed')}       : {failed}\n"
            f"  {_('batch_score')}  : {batch_score:.1f}\n"
            f"{'='*40}\n"
        )
        self.update_status(summary)
        logger.info(
            "Batch finished — total=%d, success=%d, failed=%d, score=%.1f",
            total, success, failed, batch_score,
        )

        self.report_btn.configure(state="normal")

    # ------------------------------------------------------------------ #
    #  Report viewing
    # ------------------------------------------------------------------ #

    def view_report(self) -> None:
        """Generate the HTML report and open it in the default browser."""
        try:
            report_path = self.analytics.generate_report()
            self.update_status(f"{_('report_saved')}: {report_path}")
            webbrowser.open(f"file://{os.path.abspath(report_path)}")
        except Exception as exc:
            logger.exception("Failed to generate or open report")
            self.update_status(f"{_('error_report')}: {exc}")

    # ------------------------------------------------------------------ #
    #  Status updates
    # ------------------------------------------------------------------ #

    def update_status(self, message: str) -> None:
        """Append a message to the status text area.

        Args:
            message: Text to display.
        """
        self.status_text.configure(state="normal")
        self.status_text.insert("end", message + "\n")
        self.status_text.see("end")
        self.status_text.configure(state="disabled")
        logger.info(message)

    # ------------------------------------------------------------------ #
    #  Run
    # ------------------------------------------------------------------ #

    def run(self) -> None:
        """Start the GUI main loop."""
        self.root.mainloop()
