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

from ..cms_edit.conversion.from_layers import layer_hierarchy_to_solution
from ..cms_edit.conversion.to_layers import solution_to_layer_hierarchy
from ..configuration.project_settings import DEFAULT_PROJECT_SETTINGS
from ..configuration.settings import read_project_setting
from ..constants import VERSION, PROJECT_NAME
from ..entry_points.cad_area.cad_area_dialog import CadAreaDialog
from ..utilities import resolve_path, get_icon_path
from integration_system import get_cms_solution

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

        self.changes_label.setText("")
        self.sync_button.setEnabled(False)
        self.upload_button.setEnabled(False)

        reconnect_signal(self.reload_button.clicked, self.reload_button_clicked)
        reconnect_signal(self.sync_button.clicked, self.sync_button_clicked)
        reconnect_signal(self.upload_button.clicked, self.upload_button_clicked)

        self.solution_combo_box.clear()
        self.solution_combo_box.addItems(["nhl", "kemper", "phoenix", "kingfisher"])

        # from .. import entry_points
        # print(dir(entry_points))

        self.entry_point_dialogs = {"Cad Area": CadAreaDialog()}

        if False:
            self.repopulate_grid_layout()

    def reload_button_clicked(self):
        self.changes_label.setText("Fetching venues")
        self.sync_button.setEnabled(True)
        self.upload_button.setEnabled(True)

        env_vars = dict(
            mapsindoors__username="automation@mapspeople.com",
            mapsindoors__password="8CtM6hLScJcYKtSJ6sBKqqPEBH7wBiHD",
            mapsindoors__integration_api_host=(
                "https://integration-automation.mapsindoors.com"
            ),
            mapsindoors__token_endpoint="https://auth.mapsindoors.com/connect/token",
            mapsindoors__manager_api_host="https://v2.mapsindoors.com",
        )
        os.environ.update(**env_vars)
        solution_external_id = str(self.solution_combo_box.currentText())
        self.solution = get_cms_solution(solution_external_id)

        self.venues_map = {v.name: v.external_id for v in self.solution.venues}

        self.venue_combo_box.clear()
        self.venue_combo_box.addItems([*self.venues_map.keys()])

        self.changes_label.setText("Fetched venues")

    def sync_button_clicked(self):
        venue_name = str(self.venue_combo_box.currentText())
        self.changes_label.setText(f"Downloading {venue_name}")
        solution_to_layer_hierarchy(self, self.solution, self.venues_map, venue_name)
        self.changes_label.setText(f"Downloaded {venue_name}")

    def upload_button_clicked(self):
        venue_name = str(self.venue_combo_box.currentText())
        self.changes_label.setText(f"Uploading {venue_name}")
        layer_hierarchy_to_solution()
        self.changes_label.setText(f"Uploaded {venue_name}")

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
