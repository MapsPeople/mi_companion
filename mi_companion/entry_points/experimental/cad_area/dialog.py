from pathlib import Path

import logging
from qgis.PyQt import QtWidgets, uic

from jord.qgis_utilities.helpers import signals
from mi_companion import RESOURCE_BASE_PATH
from warg import first

_logger = logging.getLogger(RESOURCE_BASE_PATH)

__all__ = ["Dialog"]


class Dialog(
    QtWidgets.QDialog, first(uic.loadUiType(str(Path(__file__).parent / "dialog.ui")))
):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        signals.reconnect_signal(self.compute_button.clicked, self.on_compute_clicked)

    def on_compute_clicked(self) -> None:
        from .cad_area_impl import run

        out_path = Path(str(self.out_file_widget.filePath()))
        in_paths = str(self.compute_files_widget.filePath())

        if in_paths.startswith('"') and in_paths.endswith('"'):
            files = in_paths.lstrip('"').rstrip('"').split('" "')
        else:
            files = [in_paths]

        for p in files:
            run(Path(p), out_path)

        self.close()
