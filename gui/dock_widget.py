import logging

from integration_system.cms.config import Settings

LOGGER = logging.getLogger(__name__)
import math
import os
from pathlib import Path
from typing import Any

from integration_client import Dataset

# from warg import ensure_in_sys_path
# ensure_in_sys_path(Path(__file__).parent.parent / "cms_edit", resolve=True)

from integration_client.rest import ApiException

from integration_system.cms import (
    get_solution_id,
    get_integration_api_client,
)
from jord.qgis_utilities import plugin_version
from jord.qgis_utilities.helpers import signals
from jord.qlive_utilities import add_shapely_layer

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtGui, QtWidgets, uic

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import pyqtSignal

# noinspection PyUnresolvedReferences
from qgis.core import (
    QgsApplication,
    QgsFeature,
    QgsGeometry,
    QgsLayerTree,
    QgsLayerTreeModel,
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
)
from warg import reload_module

from integration_system.cms.downloading import (
    get_geodata_collection,
)
from ..cms_edit import layer_hierarchy_to_solution, solution_to_layer_hierarchy
from ..configuration.project_settings import DEFAULT_PROJECT_SETTINGS
from ..configuration.settings import read_project_setting
from ..constants import PROJECT_NAME, VERSION
from ..entry_points.cad_area import CadAreaDialog
from ..entry_points.instance_rooms import InstanceRoomsDialog
from ..utilities.paths import get_icon_path, resolve_path
from ..utilities.string_parsing import extract_wkt_elements

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
        self.sync_module_settings = Settings()

        self.setupUi(self)

        self.icon_label.setPixmap(QtGui.QPixmap(get_icon_path("mp_notext.png")))
        self.sponsor_label.setPixmap(QtGui.QPixmap(get_icon_path("mp_notext.png")))

        self.version_label.setText(VERSION)
        self.plugin_status_label.setText(plugin_version.plugin_status(PROJECT_NAME))

        self.changes_label.setText("")
        self.sync_button.setEnabled(False)
        self.upload_button.setEnabled(False)

        signals.reconnect_signal(
            self.solution_reload_button.clicked, self.refresh_solution_combo_box
        )
        signals.reconnect_signal(
            self.venue_reload_button.clicked, self.refresh_venue_button_clicked
        )
        signals.reconnect_signal(self.sync_button.clicked, self.download_button_clicked)
        signals.reconnect_signal(self.upload_button.clicked, self.upload_button_clicked)

        # from .. import entry_points
        # print(dir(entry_points))

        self.entry_point_dialogs = {
            "Cad Area": CadAreaDialog(),
            "Instance Rooms": InstanceRoomsDialog(),
        }

        if True:
            self.repopulate_grid_layout()

    def set_os_environment(self):
        if False:
            env_vars = dict(
                mapsindoors__username=read_project_setting(
                    "MAPS_INDOORS_USERNAME",
                    defaults=DEFAULT_PROJECT_SETTINGS,
                    project_name=PROJECT_NAME,
                ),
                mapsindoors__password=read_project_setting(
                    "MAPS_INDOORS_PASSWORD",
                    defaults=DEFAULT_PROJECT_SETTINGS,
                    project_name=PROJECT_NAME,
                ),
                mapsindoors__integration_api_host=read_project_setting(
                    "MAPS_INDOORS_INTEGRATION_API_HOST",
                    defaults=DEFAULT_PROJECT_SETTINGS,
                    project_name=PROJECT_NAME,
                ),
                mapsindoors__token_endpoint=read_project_setting(
                    "MAPS_INDOORS_TOKEN_ENDPOINT",
                    defaults=DEFAULT_PROJECT_SETTINGS,
                    project_name=PROJECT_NAME,
                ),
                mapsindoors__manager_api_host=read_project_setting(
                    "MAPS_INDOORS_MANAGER_API_HOST",
                    defaults=DEFAULT_PROJECT_SETTINGS,
                    project_name=PROJECT_NAME,
                ),
            )

            os.environ.update(**env_vars)
        else:
            self.sync_module_settings.mapsindoors.username = read_project_setting(
                "MAPS_INDOORS_USERNAME",
                defaults=DEFAULT_PROJECT_SETTINGS,
                project_name=PROJECT_NAME,
            )

            self.sync_module_settings.mapsindoors.password = read_project_setting(
                "MAPS_INDOORS_PASSWORD",
                defaults=DEFAULT_PROJECT_SETTINGS,
                project_name=PROJECT_NAME,
            )

    def refresh_solution_combo_box(self):
        self.set_os_environment()
        self.solution_combo_box.clear()

        api_client = get_integration_api_client(settings=self.sync_module_settings)
        self.fetched_solution: list[Dataset] = api_client.call_api(
            resource_path="/api/dataset",
            method="GET",
            header_params={
                "Accept": "application/json",
                "Authorization": f"Bearer {api_client.configuration.access_token}",
            },
            response_type="list[Dataset]",
            _return_http_data_only=True,
        )
        self.solution_combo_box.addItems([s.name for s in self.fetched_solution])

    def refresh_venue_button_clicked(self) -> None:
        self.changes_label.setText("Fetching venues")
        self.sync_button.setEnabled(True)
        self.upload_button.setEnabled(True)

        self.solution_external_id = str(self.solution_combo_box.currentText())

        self.venues = get_geodata_collection(
            solution_id=get_solution_id(
                self.solution_external_id, settings=self.sync_module_settings
            ),
            base_types=["venue"],
            settings=self.sync_module_settings,
        ).get_venues()

        self.venue_name_id_map = {
            v.properties["name@en"]: v.external_id for v in self.venues
        }

        self.venue_combo_box.clear()
        self.venue_combo_box.addItems([*self.venue_name_id_map.keys()])

        self.changes_label.setText("Fetched venues")

    def download_button_clicked(self) -> None:
        venue_name = str(self.venue_combo_box.currentText())
        if venue_name.strip() == "":  # TODO: Not supported ATM
            for v in self.venue_name_id_map.values():
                solution_to_layer_hierarchy(
                    self,
                    self.solution_external_id,
                    v,
                    settings=self.sync_module_settings,
                )
        else:
            if venue_name in self.venue_name_id_map:
                self.changes_label.setText(f"Downloading {venue_name}")
                solution_to_layer_hierarchy(
                    self,
                    self.solution_external_id,
                    self.venue_name_id_map[venue_name],
                    settings=self.sync_module_settings,
                )
                self.changes_label.setText(f"Downloaded {venue_name}")
            else:
                LOGGER.warning(f"Venue {venue_name} not found")

    def upload_button_clicked(self) -> None:
        venue_name = str(self.venue_combo_box.currentText())
        self.changes_label.setText(f"Uploading {venue_name}")
        try:
            layer_hierarchy_to_solution()
        except Exception as e:
            self.display_geometry_in_exception(e)

            raise e
        self.changes_label.setText(f"Uploaded {venue_name}")

    def display_geometry_in_exception(self, e: ApiException) -> None:
        # string_exception = "\n".join(e.args)
        string_exception = str(e)
        rese = zip(*extract_wkt_elements(string_exception))
        if rese:
            contexts, elements = rese

            contexts = [clean_str(c) for c in contexts]

            add_shapely_layer(
                self,
                elements,
                name="exceptions",
                columns=[{"contexts": c} for c in contexts],
            )

    def repopulate_grid_layout(self) -> None:
        num_columns = int(
            read_project_setting(
                "NUM_COLUMNS",
                defaults=DEFAULT_PROJECT_SETTINGS,
                project_name=PROJECT_NAME,
            )
        )
        for i, (k, dialog) in enumerate(self.entry_point_dialogs.items()):
            button = QtWidgets.QPushButton(k)
            signals.reconnect_signal(button.clicked, dialog.show)

            self.entry_point_grid.addWidget(
                button, math.floor(i / num_columns), i % num_columns
            )

    # noinspection PyPep8Naming
    def closeEvent(self, event) -> None:  # pylint: disable=invalid-name
        self.plugin_closing.emit()
        event.accept()


def clean_str(s: str) -> str:
    import re

    return re.compile(r"\W+").sub(" ", s).strip()[:200]

    # return s.translate({ord("\n"): None})
