from pathlib import Path

import qgis
from qgis.PyQt import QtWidgets
from qgis.PyQt import uic

FORM_CLASS, _ = uic.loadUiType(str(Path(__file__).parent / "base_dialog.ui"))

__all__ = ["BaseDialog"]


class BaseDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

    def on_compute_clicked(self):
        file_name = self.profileNameInput.text()
        if file_name == "":
            qgis.core.QgsMessageLog.logMessage(
                "Profile: No Profile file name specified. Aborting.", level=2
            )
            message_bar = self.iface.messageBar().createMessage(
                "No Profile file name specified. Aborting.",
            )
            self.iface.messageBar().pushWidget(message_bar, 2)
            self.message_bar = message_bar
            return
