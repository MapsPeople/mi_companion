import logging
import math
import os
from pathlib import Path
from typing import Any

from integration_client.integration_model.dataset import Dataset
from integration_client.rest import ApiException
from jord.qgis_utilities import plugin_version, read_plugin_setting
from jord.qgis_utilities.helpers import signals, DialogProgressBar
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

from integration_system.cms import (
    get_solution_id,
    get_integration_api_client,
)
from integration_system.cms.config import Settings
from integration_system.cms.downloading import (
    get_geodata_collection,
)
from ..cms_edit import layer_hierarchy_to_solution, solution_to_layer_hierarchy
from ..configuration.project_settings import DEFAULT_PLUGIN_SETTINGS
from ..constants import PROJECT_NAME, VERSION
from ..entry_points.cad_area import CadAreaDialog
from ..entry_points.instance_rooms import InstanceRoomsDialog
from ..utilities.paths import get_icon_path, resolve_path
from ..utilities.string_parsing import extract_wkt_elements

# from warg import ensure_in_sys_path
# ensure_in_sys_path(Path(__file__).parent.parent / "cms_edit", resolve=True)

FORM_CLASS, _ = uic.loadUiType(resolve_path("dock_widget.ui", __file__))

signals.IS_DEBUGGING = True
logger = logging.getLogger(__name__)
VERBOSE = True
LOGGER = logger


class GdsCompanionDockWidget(QtWidgets.QDockWidget, FORM_CLASS):
    plugin_closing = pyqtSignal()

    def __init__(self, iface: Any, parent: Any = None):
        """Constructor."""
        super().__init__(parent)

        # INITIALISATION OF ATTRS
        self.fetched_solution = None
        self.venues = None
        self.solution_external_id = None
        #

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

    def set_update_sync_settings(self):
        self.sync_module_settings.mapsindoors.username = read_plugin_setting(
            "MAPS_INDOORS_USERNAME",
            default_value=DEFAULT_PLUGIN_SETTINGS["MAPS_INDOORS_USERNAME"],
            project_name=PROJECT_NAME,
        )

        self.sync_module_settings.mapsindoors.password = read_plugin_setting(
            "MAPS_INDOORS_PASSWORD",
            default_value=DEFAULT_PLUGIN_SETTINGS["MAPS_INDOORS_PASSWORD"],
            project_name=PROJECT_NAME,
        )

        self.sync_module_settings.mapsindoors.integration_api_host = (
            read_plugin_setting(
                "MAPS_INDOORS_INTEGRATION_API_HOST",
                default_value=DEFAULT_PLUGIN_SETTINGS[
                    "MAPS_INDOORS_INTEGRATION_API_HOST"
                ],
                project_name=PROJECT_NAME,
            )
        )
        self.sync_module_settings.mapsindoors.token_endpoint = read_plugin_setting(
            "MAPS_INDOORS_TOKEN_ENDPOINT",
            default_value=DEFAULT_PLUGIN_SETTINGS["MAPS_INDOORS_TOKEN_ENDPOINT"],
            project_name=PROJECT_NAME,
        )
        self.sync_module_settings.mapsindoors.manager_api_host = read_plugin_setting(
            "MAPS_INDOORS_MANAGER_API_HOST",
            default_value=DEFAULT_PLUGIN_SETTINGS["MAPS_INDOORS_MANAGER_API_HOST"],
            project_name=PROJECT_NAME,
        )
        self.sync_module_settings.mapsindoors.media_api_host = read_plugin_setting(
            "MAPS_INDOORS_MEDIA_API_HOST",
            default_value=DEFAULT_PLUGIN_SETTINGS["MAPS_INDOORS_MEDIA_API_HOST"],
            project_name=PROJECT_NAME,
        )

    def refresh_solution_combo_box(self):
        self.set_update_sync_settings()
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
        self.set_update_sync_settings()

        with DialogProgressBar() as bar:
            self.solution_external_id = str(self.solution_combo_box.currentText())
            bar.setValue(10)

            solution_id = get_solution_id(
                self.solution_external_id, settings=self.sync_module_settings
            )
            if solution_id is None:
                logger.error(
                    f"Could not find solution id for {self.solution_external_id}"
                )
                return
            bar.setValue(30)

            self.venues = get_geodata_collection(
                solution_id,
                base_types=["venue"],
                settings=self.sync_module_settings,
            ).get_venues()
            bar.setValue(90)

            self.venue_name_id_map = {
                v.properties["name@en"]: v.external_id for v in self.venues
            }

            self.venue_combo_box.clear()
            self.venue_combo_box.addItems([*self.venue_name_id_map.keys()])
            bar.setValue(100)

            self.changes_label.setText("Fetched venues")

    def download_button_clicked(self) -> None:
        venue_name = str(self.venue_combo_box.currentText())
        with DialogProgressBar() as bar:
            if venue_name.strip() == "":  # TODO: Not supported ATM
                venues = list(self.venue_name_id_map.values())
                num_venues = float(len(venues))
                for i, v in enumerate(venues):
                    with DialogProgressBar() as venue_bar:
                        solution_to_layer_hierarchy(
                            self,
                            self.solution_external_id,
                            v,
                            settings=self.sync_module_settings,
                            progress_bar=venue_bar,
                        )
                    bar.setValue(int((float(i) / num_venues) * 100))
            else:
                if venue_name in self.venue_name_id_map:
                    self.changes_label.setText(f"Downloading {venue_name}")
                    solution_to_layer_hierarchy(
                        self,
                        self.solution_external_id,
                        self.venue_name_id_map[venue_name],
                        settings=self.sync_module_settings,
                        progress_bar=bar,
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
            read_plugin_setting(
                "NUM_COLUMNS",
                default_value=DEFAULT_PLUGIN_SETTINGS["NUM_COLUMNS"],
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
