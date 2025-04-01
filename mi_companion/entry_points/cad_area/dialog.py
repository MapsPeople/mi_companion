import logging
import os
from pathlib import Path

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets, uic

from jord.qgis_utilities.helpers import signals

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "cad_area_dialog.ui")
)

logger = logging.getLogger(__name__)

__all__ = ["Dialog"]


class Dialog(QtWidgets.QDialog, FORM_CLASS):

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
