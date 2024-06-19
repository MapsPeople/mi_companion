def run():
    # noinspection PyUnresolvedReferences
    from qgis.utils import iface

    from .level_selector import LevelSelectorWidget

    return LevelSelectorWidget(iface.mainWindow())


__all__ = ["ENTRY_POINT_NAME", "ENTRY_POINT_DIALOG"]

ENTRY_POINT_NAME = " ".join(s.capitalize() for s in __name__.split(".")[-1].split("_"))
ENTRY_POINT_DIALOG = run
