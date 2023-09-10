import math
import os
from pathlib import Path
from typing import Any

from jord.qgis_utilities import (
    plugin_status,
    reconnect_signal,
)
from jord.qgis_utilities.helpers import signals

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtGui, QtWidgets, uic

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import pyqtSignal

# noinspection PyUnresolvedReferences
from qgis.core import (
    QgsVectorLayer,
    QgsRasterLayer,
    QgsProject,
    QgsLayerTreeModel,
    QgsLayerTree,
    QgsGeometry,
    QgsFeature,
    QgsApplication,
)
from warg import reload_module

from ..configuration.project_settings import DEFAULT_PROJECT_SETTINGS
from ..configuration.settings import read_project_setting
from ..constants import VERSION, PROJECT_NAME
from ..entry_points.cad_area.cad_area_dialog import CadAreaDialog
from ..utilities import resolve_path, get_icon_path

FORM_CLASS, _ = uic.loadUiType(resolve_path("dock_widget.ui", __file__))

signals.IS_DEBUGGING = True

VERBOSE = True


class GdsCompanionDockWidget(QtWidgets.QDockWidget, FORM_CLASS):
    plugin_closing = pyqtSignal()

    def __init__(self, iface: Any, parent: Any = None):
        """Constructor."""
        super().__init__(parent)
        self.iface = iface
        self.qgis_project = QgsProject.instance()

        if VERBOSE:
            reload_module("jord")
            reload_module("warg")

        self.plugin_dir = Path(os.path.dirname(__file__))

        self.setupUi(self)

        self.icon_label.setPixmap(QtGui.QPixmap(get_icon_path("mp_notext.png")))
        self.sponsor_label.setPixmap(QtGui.QPixmap(get_icon_path("mp_notext.png")))

        self.version_label.setText(VERSION)
        self.plugin_status_label.setText(plugin_status(PROJECT_NAME))

        # from .. import entry_points
        # print(dir(entry_points))

        self.entry_point_dialogs = {"Cad Area": CadAreaDialog()}

        self.repopulate_grid_layout()

    def repopulate_grid_layout(self):
        num_columns = int(
            read_project_setting(
                "NUM_COLUMNS",
                defaults=DEFAULT_PROJECT_SETTINGS,
                project_name=PROJECT_NAME,
            )
        )
        for i, (k, dialog) in enumerate(self.entry_point_dialogs.items()):
            button = QtWidgets.QPushButton(k)
            reconnect_signal(button.clicked, dialog.show)

            self.entry_point_grid.addWidget(
                button, math.floor(i / num_columns), i % num_columns
            )

    # noinspection PyPep8Naming
    def closeEvent(self, event) -> None:  # pylint: disable=invalid-name
        self.plugin_closing.emit()
        event.accept()
