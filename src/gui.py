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

        # Core components
        self.vision = VisionProcessor(config=self.config)
        self.analytics = AnalyticsEngine(config=self.config)

        # --- Main window ------------------------------------------------ #
        self.root = ctk.CTk()
        self.root.title("OMR QA Form Scanner")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)

        self._create_widgets()

    # ------------------------------------------------------------------ #
    #  Widget creation
    # ------------------------------------------------------------------ #

    def _create_widgets(self) -> None:
        """Build all UI elements."""
        # Header
        self.header = ctk.CTkLabel(
            self.root,
            text="OMR QA Form Scanner",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        self.header.pack(pady=(20, 10))

        # Folder selection frame
        self.folder_frame = ctk.CTkFrame(self.root)
        self.folder_frame.pack(padx=20, pady=10, fill="x")

        self.folder_label = ctk.CTkLabel(
            self.folder_frame,
            text="No folder selected",
            font=ctk.CTkFont(size=12),
            wraplength=700,
        )
        self.folder_label.pack(side="left", padx=10, pady=10)

        self.browse_btn = ctk.CTkButton(
            self.folder_frame,
            text="Browse",
            command=self.select_input_folder,
            width=100,
        )
        self.browse_btn.pack(side="right", padx=10, pady=10)

        # Image count label
        self.count_label = ctk.CTkLabel(
            self.root,
            text="Images found: 0",
            font=ctk.CTkFont(size=12),
        )
        self.count_label.pack(pady=5)

        # Action buttons
        self.btn_frame = ctk.CTkFrame(self.root)
        self.btn_frame.pack(padx=20, pady=10, fill="x")

        self.start_btn = ctk.CTkButton(
            self.btn_frame,
            text="Start Processing",
            command=self.start_processing,
            state="disabled",
            width=150,
        )
        self.start_btn.pack(side="left", padx=10, pady=10)

        self.report_btn = ctk.CTkButton(
            self.btn_frame,
            text="View & Print Report",
            command=self.view_report,
            state="disabled",
            width=150,
        )
        self.report_btn.pack(side="right", padx=10, pady=10)

        # Status / progress area
        self.status_frame = ctk.CTkFrame(self.root)
        self.status_frame.pack(padx=20, pady=10, fill="both", expand=True)

        self.status_text = ctk.CTkTextbox(
            self.status_frame,
            wrap="word",
            font=ctk.CTkFont(size=12),
        )
        self.status_text.pack(padx=10, pady=10, fill="both", expand=True)
        self.status_text.insert("0.0", "Welcome. Select an input folder to begin.\n")
        self.status_text.configure(state="disabled")

    # ------------------------------------------------------------------ #
    #  Folder selection
    # ------------------------------------------------------------------ #

    def select_input_folder(self) -> None:
        """Open a folder dialog and validate the selection."""
        folder = filedialog.askdirectory(title="Select Input Folder")
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
        self.count_label.configure(text=f"Images found: {count}")
        self.update_status(f"Found {count} image(s) in {self.input_folder.name}")

        if count > 0:
            self.start_btn.configure(state="normal")
        else:
            self.start_btn.configure(state="disabled")
            self.update_status("No supported images found. Add .jpg or .png files.")

        # Reset report button
        self.report_btn.configure(state="disabled")

    # ------------------------------------------------------------------ #
    #  Processing
    # ------------------------------------------------------------------ #

    def start_processing(self) -> None:
        """Process all image files in the selected folder."""
        if not self.image_files:
            self.update_status("No images to process.")
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
            self.update_status(f"[{idx}/{total}] Processing {img_path.name} ...")
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
            f"Batch complete!\n"
            f"  Total images : {total}\n"
            f"  Successful   : {success}\n"
            f"  Failed       : {failed}\n"
            f"  Batch score  : {batch_score:.1f}\n"
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
            self.update_status(f"Report saved to: {report_path}")
            webbrowser.open(f"file://{os.path.abspath(report_path)}")
        except Exception as exc:
            logger.exception("Failed to generate or open report")
            self.update_status(f"Error generating report: {exc}")

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
