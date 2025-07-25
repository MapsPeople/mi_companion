import logging
from typing import Any

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtGui import QIcon

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QWidget,
)

# noinspection PyUnresolvedReferences
from qgis.core import Qgis, QgsGeometry, QgsMessageLog

# noinspection PyUnresolvedReferences
from qgis.gui import (
    QgsMessageBar,
)

# noinspection PyUnresolvedReferences
from qgis.utils import iface

from jord.qgis_utilities import read_plugin_setting
from mi_companion import (
    DEFAULT_PLUGIN_SETTINGS,
    MAPS_INDOORS_QGIS_PLUGIN_TITLE,
    PROJECT_NAME,
)

logger = logging.getLogger(__name__)

__all__ = [
    "make_hierarchy_validation_dialog",
    "make_validation_action_toast",
    "make_temporary_toast",
]


def make_hierarchy_validation_dialog(
    header: str,
    message: str,
    *,
    accept_text: str = "Okay",
    add_reject_option: bool = False,
    reject_text: str = "Undo",
    alternative_accept_text: str = "Ignore",
    minimum_header_padding: int = 200,
    level=QMessageBox.Critical,
) -> Any:
    logger.error(message)

    resource_path = read_plugin_setting(
        "RESOURCES_BASE_PATH",
        default_value=DEFAULT_PLUGIN_SETTINGS["RESOURCES_BASE_PATH"],
        project_name=PROJECT_NAME,
    )

    if False:  # DOES NOT WORK!!!
        header_length = len(header)
        if header_length < minimum_header_padding:
            size = (minimum_header_padding - header_length) // 2
            pad = " " * size
            if False:
                header = pad + header + pad
            else:
                header += pad * 2

            header += "."

    header = "<b>" + header + "</b>"

    qt_msg_box = QMessageBox()
    qt_msg_box.setWindowIcon(QIcon(f"{resource_path}/icons/mp-favicon-white.png"))
    qt_msg_box.setWindowTitle(MAPS_INDOORS_QGIS_PLUGIN_TITLE)
    qt_msg_box.setIcon(level)
    qt_msg_box.setText(header)
    qt_msg_box.setInformativeText(message)

    if False:
        qt_msg_box.findChild(QGridLayout).setColumnMinimumWidth(
            1,
            len(qt_msg_box.informativeText())
            * qt_msg_box.fontMetrics().averageCharWidth()
            // 4,
        )
    else:
        layout = qt_msg_box.layout()
        layout.setColumnMinimumWidth(layout.columnCount() - 1, 300)

    if add_reject_option:
        reject_button = qt_msg_box.addButton(reject_text, QMessageBox.RejectRole)
        accept_button = qt_msg_box.addButton(
            alternative_accept_text, QMessageBox.AcceptRole
        )

        default_button = reject_button
    else:
        accept_button = qt_msg_box.addButton(accept_text, QMessageBox.AcceptRole)
        default_button = accept_button

    qt_msg_box.setDefaultButton(default_button)

    res = qt_msg_box.exec()

    if qt_msg_box.clickedButton() == accept_button:
        return QMessageBox.AcceptRole

    return QMessageBox.RejectRole


def make_validation_action_toast(
    header: str,
    message: str,
    *,
    add_reject_option: bool = False,
    reject_text: str = "Undo",
    accept_text: str = "Okay",
):
    def showError():
        pass

    widget = iface.messageBar().createMessage("Missing Layers", "Show Me")
    button = QPushButton(widget)
    button.setText("Show Me")
    button.pressed.connect(showError)
    widget.layout().addWidget(button)
    iface.messageBar().pushWidget(widget, Qgis.Warning)


def wah():
    ...
    """
import time

progressMessageBar = iface.messageBar().createMessage("Doing something boring...")
progress = QtWidgets.QProgressBar()
progress.setMaximum(10)
progress.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
progressMessageBar.layout().addWidget(progress)
iface.messageBar().pushWidget(progressMessageBar, Qgis.Info)

for i in range(10):
    time.sleep(1)
    progress.setValue(i + 1)

iface.messageBar().clearWidgets()
"""


def wah2():
    class MyDialog(QDialog):

        def __init__(self):
            QDialog.__init__(self)
            self.bar = QgsMessageBar()
            self.bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
            self.setLayout(QGridLayout())
            self.layout().setContentsMargins(0, 0, 0, 0)
            self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok)
            self.buttonbox.accepted.connect(self.run)
            self.layout().addWidget(self.buttonbox, 0, 0, 2, 1)
            self.layout().addWidget(self.bar, 0, 0, 1, 1)

        def run(self):
            self.bar.pushMessage("Hello", "World", level=Qgis.Info)

    myDlg = MyDialog()
    myDlg.show()


def make_temporary_toast(message, level=Qgis.Info, duration=3):
    iface.messageBar().pushMessage(
        MAPS_INDOORS_QGIS_PLUGIN_TITLE, message, level=level, duration=duration
    )
