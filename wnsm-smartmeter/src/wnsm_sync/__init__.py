"""Wiener Netze Smart Meter Sync for Home Assistant."""

__version__ = "1.0.0"
__author__ = "WNSM Sync Contributors"
__description__ = "Home Assistant add-on for syncing Wiener Netze Smart Meter data"

from .core.sync import WNSMSync

__all__ = ["WNSMSync"]