"""Backward-compatibility shim — SettingsFrame moved to src/pages/settings.py."""

from pages.settings import SettingsFrame  # noqa: F401

__all__ = ["SettingsFrame"]
