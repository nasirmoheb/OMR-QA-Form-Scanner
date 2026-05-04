"""Internationalisation: English, Dari, and Pashto translations."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("omr_qa_scanner")

# --------------------------------------------------------------------------- #
#  Translation dictionaries
# --------------------------------------------------------------------------- #

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "app_title": "OMR QA Form Scanner",
        "browse": "Browse",
        "start_processing": "Start Processing",
        "view_report": "View & Print Report",
        "settings": "Settings",
        "language": "Language",
        "appearance": "Appearance",
        "light": "Light",
        "dark": "Dark",
        "system": "System",
        "select_folder": "Select Input Folder",
        "no_folder": "No folder selected",
        "images_found": "Images found: {count}",
        "welcome": "Welcome. Select an input folder to begin.",
        "batch_complete": "Batch complete!",
        "total_images": "Total images",
        "successful": "Successful",
        "failed": "Failed",
        "batch_score": "Batch score",
        "processing": "Processing",
        "report_saved": "Report saved to",
        "error_report": "Error generating report",
        "no_images": "No images to process.",
        "no_supported": "No supported images found. Add .jpg or .png files.",
        "save": "Save",
        "cancel": "Cancel",
        "general": "General",
        "form_geometry": "Form Geometry",
        "form_width": "Form Width",
        "form_height": "Form Height",
        "threshold": "Checkbox Threshold",
        "rows": "Rows",
        "columns": "Columns",
        "score_yes": "Score (Yes)",
        "score_somewhat": "Score (Somewhat)",
        "score_no": "Score (No)",
        "settings_saved": "Settings saved successfully.",
        "restart_required": "Restart the application to apply all changes.",
        "close": "Close",
        "dashboard": "Dashboard",
        "new_survey": "New Survey",
        "edit_survey": "Edit Survey",
        "process": "Process",
        "results": "Results",
        "delete": "Delete",
        "confirm_delete": "Are you sure you want to delete this survey?",
        "draft": "Draft",
        "processed": "Processed",
        "analyzed": "Analyzed",
        "subject": "Subject",
        "professor": "Professor",
        "semester": "Semester",
        "academic_year": "Academic Year",
        "department": "Department",
        "search": "Search...",
        "filter_dept": "Filter by Department",
        "all_departments": "All Departments",
        "university": "University",
        "faculty": "Faculty",
        "professor_name": "Professor Name",
        "save_survey": "Save Survey",
        "print_form": "Print Survey Form",
        "back": "Back",
        "no_surveys": "No surveys found. Click 'New Survey' to create one.",
    },
    "fa": {
        "app_title": "اسکنر فورم تضمین کیفیت OMR",
        "browse": "جستجو",
        "start_processing": "شروع پردازش",
        "view_report": "مشاهده و چاپ گزارش",
        "settings": "تنظیمات",
        "language": "زبان",
        "appearance": "ظاهر",
        "light": "روشن",
        "dark": "تاریک",
        "system": "سیستم",
        "select_folder": "انتخاب پوشه ورودی",
        "no_folder": "هیچ پوشه‌ای انتخاب نشده",
        "images_found": "تصاویر یافت شده: {count}",
        "welcome": "خوش آمدید. یک پوشه ورودی را برای شروع انتخاب کنید.",
        "batch_complete": "پردازش دسته‌ای تکمیل شد!",
        "total_images": "تعداد تصاویر",
        "successful": "موفق",
        "failed": "ناموفق",
        "batch_score": "نمره دسته‌ای",
        "processing": "در حال پردازش",
        "report_saved": "گزارش ذخیره شد در",
        "error_report": "خطا در تولید گزارش",
        "no_images": "تصویری برای پردازش وجود ندارد.",
        "no_supported": "تصاویر پشتیبانی شده یافت نشد. فایل‌های .jpg یا .png اضافه کنید.",
        "save": "ذخیره",
        "cancel": "لغو",
        "general": "عمومی",
        "form_geometry": "ابعاد فورم",
        "form_width": "عرض فورم",
        "form_height": "ارتفاع فورم",
        "threshold": "آستانه چک‌باکس",
        "rows": "ردیف‌ها",
        "columns": "ستون‌ها",
        "score_yes": "نمره (بله)",
        "score_somewhat": "نمره (تا حدی)",
        "score_no": "نمره (خیر)",
        "settings_saved": "تنظیمات با موفقیت ذخیره شد.",
        "restart_required": "برای اعمال تمام تغییرات، برنامه را مجدداً راه‌اندازی کنید.",
        "close": "بستن",
        "dashboard": "داشبورد",
        "new_survey": "نظرسنجی جدید",
        "edit_survey": "ویرایش نظرسنجی",
        "process": "پردازش",
        "results": "نتایج",
        "delete": "حذف",
        "confirm_delete": "آیا مطمئن هستید که می‌خواهید این نظرسنجی را حذف کنید؟",
        "draft": "پیش‌نویس",
        "processed": "پردازش شده",
        "analyzed": "تحلیل شده",
        "subject": "موضوع",
        "professor": "استاد",
        "semester": "ترم",
        "academic_year": "سال تحصیلی",
        "department": "دانشکده",
        "search": "جستجو...",
        "filter_dept": "فیلتر بر اساس دانشکده",
        "all_departments": "همه دانشکده‌ها",
        "university": "دانشگاه",
        "faculty": " دانشکده",
        "professor_name": "نام استاد",
        "save_survey": "ذخیره نظرسنجی",
        "print_form": "چاپ فرم نظرسنجی",
        "back": "بازگشت",
        "no_surveys": "نظرسنجی یافت نشد. برای ایجاد یک نظرسنجی جدید روی 'نظرسنجی جدید' کلیک کنید.",
    },
    "ps": {
        "app_title": "OMR د کیفیت تضمین فورم سکینر",
        "browse": "لټون",
        "start_processing": "د پروسس پیل",
        "view_report": "راپور کتنه او چاپ",
        "settings": "ترتیبات",
        "language": "ژبه",
        "appearance": "ښکاره‌دهنه",
        "light": "روښانه",
        "dark": "تیاره",
        "system": "سیسټم",
        "select_folder": "د ننوتنې فولډر وټاکئ",
        "no_folder": "هیڅ فولډر ندی ټاکل شوی",
        "images_found": "انځورونه وموندل شول: {count}",
        "welcome": "ښه راغلاست. د پیل کولو لپاره یو ننوتنې فولډر وټاکئ.",
        "batch_complete": "د ډلې پروسس بشپړ شو!",
        "total_images": "د انځورونو شمیر",
        "successful": "بریالی",
        "failed": "ناکام",
        "batch_score": "د ډلې نمره",
        "processing": "پروسس کیږي",
        "report_saved": "راپور خوندي شو",
        "error_report": "د رپورټ تولید کې تیروتنه",
        "no_images": "د پروسس کولو لپاره هیڅ انځور نشته.",
        "no_supported": "هیڅ ملاتړ شوی انځور ونه موندل شو. .jpg یا .png فایلونه اضافه کړئ.",
        "save": "خوندي کول",
        "cancel": "لغوه",
        "general": "عمومي",
        "form_geometry": "د فورم اندازې",
        "form_width": "د فورم پلنوالی",
        "form_height": "د فورم اوږدوالی",
        "threshold": "د چک‌باکس حد",
        "rows": "لیکې",
        "columns": "ستونونه",
        "score_yes": "نمره (هو)",
        "score_somewhat": "نمره (څه ناڅه)",
        "score_no": "نمره (نه)",
        "settings_saved": "ترتیبات په بریالیتوب سره خوندي شول.",
        "restart_required": "د ټولو بدلونونو د تطبیق لپاره اپلیکیشن بیا پیل کړئ.",
        "close": "تړل",
        "dashboard": "ډشبورډ",
        "new_survey": "نوی سروې",
        "edit_survey": "سروې سمون",
        "process": "پروسس",
        "results": "پايلې",
        "delete": "ړنګول",
        "confirm_delete": "آیا تاسو یقین لرئ چې غواړئ دا سروې ړنګه کړئ؟",
        "draft": "مسوده",
        "processed": "پروسس شوی",
        "analyzed": "تحلیل شوی",
        "subject": "موضوع",
        "professor": "پروفیسور",
        "semester": "سمسټر",
        "academic_year": "اکاډمیک کال",
        "department": "ډیپارټمنټ",
        "search": "لټون...",
        "filter_dept": "د ډیپارټمنټ له لارې فیلټر کړئ",
        "all_departments": "ټول ډیپارټمنټونه",
        "university": "پوهنتون",
        "faculty": "فیکلټي",
        "professor_name": "د پروفیسور نوم",
        "save_survey": "سروۍ خوندي کړئ",
        "print_form": "د سروۍ فورم چاپ کړئ",
        "back": "بیرته",
        "no_surveys": "هیڅ سروۍ ونه موندل شوه. د نوي سروۍ جوړولو لپاره 'نوي سروۍ' کلیک وکړئ.",
    },
}

# --------------------------------------------------------------------------- #
#  I18n manager
# --------------------------------------------------------------------------- #

class I18n:
    """Simple translation manager."""

    _lang: str = "en"
    _listeners: list[Any] = []

    @classmethod
    def set_language(cls, lang: str) -> None:
        """Switch active language and notify listeners."""
        if lang not in _TRANSLATIONS:
            logger.warning("Unknown language '%s', falling back to 'en'", lang)
            lang = "en"
        cls._lang = lang
        for callback in cls._listeners:
            try:
                callback()
            except Exception:
                logger.exception("I18n listener failed")

    @classmethod
    def get_language(cls) -> str:
        return cls._lang

    @classmethod
    def t(cls, key: str, **kwargs: Any) -> str:
        """Translate a key, optionally formatting it."""
        text = _TRANSLATIONS.get(cls._lang, _TRANSLATIONS["en"]).get(
            key, _TRANSLATIONS["en"].get(key, key)
        )
        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError:
                pass
        return text

    @classmethod
    def register_listener(cls, callback: Any) -> None:
        if callback not in cls._listeners:
            cls._listeners.append(callback)

    @classmethod
    def unregister_listener(cls, callback: Any) -> None:
        if callback in cls._listeners:
            cls._listeners.remove(callback)

    @classmethod
    def languages(cls) -> dict[str, str]:
        return {
            "en": "English",
            "fa": "دری (Dari)",
            "ps": "پښتو (Pashto)",
        }


# Aliases for convenience
def _(key: str, **kwargs: Any) -> str:
    return I18n.t(key, **kwargs)
