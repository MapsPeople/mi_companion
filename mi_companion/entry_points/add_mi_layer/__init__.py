from .dialog import Dialog

__all__ = ["ENTRY_POINT_NAME", "ENTRY_POINT_DIALOG", "Dialog"]

ENTRY_POINT_NAME = " ".join(s.capitalize() for s in __name__.split(".")[-1].split("_"))
ENTRY_POINT_DIALOG = Dialog
