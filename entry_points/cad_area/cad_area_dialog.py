import os
from pathlib import Path

from jord.qgis_utilities.helpers import signals

from qgis.PyQt import QtWidgets
from qgis.PyQt import uic

from .cad_area_impl import run

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "cad_area_dialog.ui")
)

__all__ = ["CadAreaDialog"]


class CadAreaDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        signals.reconnect_signal(self.compute_button.clicked, self.on_compute_clicked)

    def on_compute_clicked(self):
        out_path = Path(str(self.out_file_widget.filePath()))
        in_paths = str(self.compute_files_widget.filePath())

        if in_paths.startswith('"') and in_paths.endswith('"'):
            files = in_paths.lstrip('"').rstrip('"').split('" "')
        else:
            files = [in_paths]

        for p in files:
            run(Path(p), out_path)
