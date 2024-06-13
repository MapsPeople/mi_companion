from pathlib import Path

from .dialog import Dialog


__all__ = ["ENTRY_POINT_NAME", "ENTRY_POINT_DIALOG"]

ENTRY_POINT_NAME = Path(__file__).parent.stem.replace("_", " ").capitalize()
ENTRY_POINT_DIALOG = Dialog
