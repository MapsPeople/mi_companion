import logging
import math
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Optional

from jord.qgis_utilities import read_plugin_setting
from jord.qgis_utilities.helpers import InjectedProgressBar, signals
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

from integration_system.mi import SolutionDepth, get_venue_key_mi_venue_map
from mi_companion.mi_editor import (
    layer_hierarchy_to_solution,
    revert_venues,
    solution_venue_to_layer_hierarchy,
)
from .. import DEFAULT_PLUGIN_SETTINGS
from ..configuration.options import read_bool_setting
from ..constants import PROJECT_NAME, VERSION
from ..entry_points.compatibility import CompatibilityDialog

# from ..entry_points.cad_area import CadAreaDialog
from ..entry_points.duplicate_group import DuplicateGroupDialog
from ..entry_points.make_solution import MakeSolutionDialog
from ..entry_points.regen_feature_external_ids import RegenFeatureExternalIdsDialog
from ..entry_points.regen_group_external_ids import RegenGroupExternalIdsDialog
from ..entry_points.svg_import import SvgImportDialog
from ..mi_editor.conversion.projection import MI_EPSG_NUMBER
from ..utilities.paths import get_icon_path, resolve_path
from ..utilities.string_parsing import extract_wkt_elements

FORM_CLASS, _ = uic.loadUiType(resolve_path("dock_widget.ui", __file__))

signals.IS_DEBUGGING = True
logger = logging.getLogger(__name__)
VERBOSE = False
LOGGER = logger


class MapsIndoorsCompanionDockWidget(QtWidgets.QDockWidget, FORM_CLASS):
    plugin_closing = pyqtSignal()

    def __init__(self, iface: Any, parent: Optional[Any] = None):
        """Constructor."""
        super().__init__(parent)

        from integration_system.mi import Settings

        # INITIALISATION OF ATTRS
        self.fetched_solution = None
        self.venue_name_id_map = None
        self.venues = None
        self.solution_external_id = None
        self.external_id_map = None
        #

        self.iface = iface
        self.qgis_project = QgsProject.instance()

        # self.setModal(True)
        # self.setModal(False) # TODO: MAKE MAIN WINDOW RESPONSIVE?

        if VERBOSE:
            reload_module("jord")
            reload_module("warg")
            reload_module("integration_system")

        self.plugin_dir = Path(os.path.dirname(__file__))
        self.sync_module_settings = Settings()
        self.set_update_sync_settings()
        self.setupUi(self)

        self.icon_label.setPixmap(QtGui.QPixmap(get_icon_path("mp_notext.png")))

        self.version_label.setText(VERSION)
        # self.plugin_status_label.setText(plugin_version.plugin_status(PROJECT_NAME))

        self.changes_label.setText("")
        if False:
            self.sync_button.setEnabled(False)
            self.upload_button.setEnabled(False)

        self.original_solution_venues = defaultdict(dict)

        signals.reconnect_signal(
            self.solution_reload_button.clicked, self.refresh_solution_combo_box
        )
        signals.reconnect_signal(
            self.venue_reload_button.clicked, self.refresh_venue_button_clicked
        )
        signals.reconnect_signal(self.sync_button.clicked, self.download_button_clicked)
        signals.reconnect_signal(self.upload_button.clicked, self.upload_button_clicked)
        # signals.reconnect_signal(self.revert_button.clicked, self.revert_button_clicked)

        signals.reconnect_signal(
            self.solution_combo_box.currentIndexChanged, self.solution_combo_changed
        )
        signals.reconnect_signal(
            self.solution_combo_box.currentTextChanged, self.solution_combo_changed
        )

        self.solution_depth_combo_box = None
        if read_bool_setting("ADVANCED_MODE"):
            self.solution_depth_combo_box = None
            if False:
                self.sync_layout.addWidget(self.solution_depth_combo_box)

        # from .. import entry_points

        # print(dir(entry_points))

        self.entry_point_dialogs = {
            "Make Solution": MakeSolutionDialog(),
            "Duplicate Group": DuplicateGroupDialog(),
            # "Cad Area": CadAreaDialog(),
            "Import SVG": SvgImportDialog(),
            "Regen Group/Layer Field": RegenGroupExternalIdsDialog(),
            "Regen Selected Feature Field": RegenFeatureExternalIdsDialog(),
            # "Diff Tool": InstanceRoomsDialog(),
            "Compatibility": CompatibilityDialog(),
            # "Generate Connectors": GenerateConnectorsDialog(),
            # "Generate Doors": InstanceRoomsDialog(),
            # "Generate Walls": InstanceRoomsDialog(),
            # "Classify Location": InstanceRoomsDialog(),
        }

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

        integration_token = read_plugin_setting(
            "MAPS_INDOORS_INTEGRATION_API_TOKEN",
            default_value=DEFAULT_PLUGIN_SETTINGS["MAPS_INDOORS_INTEGRATION_API_TOKEN"],
            project_name=PROJECT_NAME,
        )
        if integration_token:
            self.sync_module_settings.mapsindoors.integration_api_bearer_token = (
                integration_token
            )

        manager_token = read_plugin_setting(
            "MAPS_INDOORS_MANAGER_API_TOKEN",
            default_value=DEFAULT_PLUGIN_SETTINGS["MAPS_INDOORS_MANAGER_API_TOKEN"],
            project_name=PROJECT_NAME,
        )
        if manager_token:
            self.sync_module_settings.mapsindoors.manager_api_bearer_token = (
                manager_token
            )

    def refresh_solution_combo_box(self, reload_venues: bool = True) -> None:
        from integration_system.mi import get_solution_name_external_id_map

        with InjectedProgressBar(
            parent=self.iface.mainWindow().statusBar()
        ) as bar:  # TODO: add a text label or format progress bar with a title
            bar.setValue(10)
            self.set_update_sync_settings()
            current_solution_name = str(self.solution_combo_box.currentText()).strip()
            logger.debug(f"{current_solution_name=}")

            bar.setValue(30)
            self.solution_combo_box.clear()
            if current_solution_name != "":
                self.solution_combo_box.setCurrentText(current_solution_name)

            bar.setValue(50)
            self.external_id_map = get_solution_name_external_id_map(
                settings=self.sync_module_settings
            )

            bar.setValue(90)
            self.solution_combo_box.addItems(sorted(self.external_id_map.keys()))

            if current_solution_name != "":
                self.solution_combo_box.setCurrentText(current_solution_name)

            bar.setValue(100)

            if reload_venues:  # auto load venue dropdown
                self.refresh_venue_button_clicked()

    def solution_combo_changed(self):
        self.venue_combo_box.clear()

    def refresh_venue_button_clicked(self) -> None:
        from integration_system.mi import (
            get_solution_id,
        )

        self.changes_label.setText("Fetching venues")
        if False:
            self.sync_button.setEnabled(True)
            self.upload_button.setEnabled(True)

        self.set_update_sync_settings()

        if self.external_id_map is None:
            self.refresh_solution_combo_box(reload_venues=False)

        with InjectedProgressBar(parent=self.iface.mainWindow().statusBar()) as bar:
            current_selected_solution_name = str(self.solution_combo_box.currentText())

            if current_selected_solution_name not in self.external_id_map:
                logger.error(
                    f"Could not find external_id for solution id for {self.solution_external_id}"
                )
                return

            self.solution_external_id = self.external_id_map[
                current_selected_solution_name
            ]
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

            self.venues = get_venue_key_mi_venue_map(
                solution_id,
                settings=self.sync_module_settings,
            )

            bar.setValue(90)

            self.venue_name_id_map = {
                next(iter(v.venueInfo))["name"]: v.externalId
                for v in self.venues.values()
            }

            self.venue_combo_box.clear()
            self.venue_combo_box.addItems(sorted(self.venue_name_id_map.keys()))
            bar.setValue(100)

            self.changes_label.setText("Fetched venues")

    def download_button_clicked(self) -> None:
        venue_name = str(self.venue_combo_box.currentText())
        if venue_name.strip() == "":
            logger.error(f"No venue was selected!")
            return

        solution_depth = SolutionDepth.LOCATIONS
        if self.solution_depth_combo_box:
            solution_depth = str(self.solution_combo_box.currentText())
        include_route_elements = read_bool_setting("ADD_DOORS")
        include_occupants = False
        include_media = False
        include_graph = read_bool_setting("ADD_GRAPH")
        with InjectedProgressBar(parent=self.iface.mainWindow().statusBar()) as bar:
            if venue_name.strip() == "":  # TODO: Not supported ATM
                venues = list(self.venue_name_id_map.values())
                num_venues = float(len(venues))
                for i, v in enumerate(venues):
                    with InjectedProgressBar(
                        parent=self.iface.mainWindow().statusBar()
                    ) as venue_bar:
                        (
                            self.original_solution_venues[self.solution_external_id][v]
                        ) = solution_venue_to_layer_hierarchy(
                            self,
                            self.solution_external_id,
                            v,
                            settings=self.sync_module_settings,
                            progress_bar=venue_bar,
                            depth=solution_depth,
                            include_route_elements=include_route_elements,
                            include_occupants=include_occupants,
                            include_media=include_media,
                            include_graph=include_graph,
                        )
                    bar.setValue(int((float(i) / num_venues) * 100))
            else:
                if venue_name in self.venue_name_id_map:
                    self.changes_label.setText(f"Downloading {venue_name}")
                    (
                        self.original_solution_venues[self.solution_external_id][
                            venue_name
                        ]
                    ) = solution_venue_to_layer_hierarchy(
                        self,
                        self.solution_external_id,
                        self.venue_name_id_map[venue_name],
                        settings=self.sync_module_settings,
                        progress_bar=bar,
                        depth=solution_depth,
                        include_route_elements=include_route_elements,
                        include_occupants=include_occupants,
                        include_media=include_media,
                        include_graph=include_graph,
                    )
                    self.changes_label.setText(f"Downloaded {venue_name}")
                else:
                    LOGGER.warning(f"Venue {venue_name} not found")

    def upload_button_clicked(self) -> None:
        self.set_update_sync_settings()

        solution_depth = SolutionDepth.LOCATIONS
        if self.solution_depth_combo_box:
            solution_depth = str(self.solution_combo_box.currentText())
        include_route_elements = False
        include_occupants = False
        include_media = False
        include_graph = False
        with InjectedProgressBar(parent=self.iface.mainWindow().statusBar()) as bar:
            self.changes_label.setText(f"Uploading venues")
            try:
                layer_hierarchy_to_solution(
                    self,
                    settings=self.sync_module_settings,
                    progress_bar=bar,
                    solution_depth=solution_depth,
                    include_route_elements=include_route_elements,
                    include_occupants=include_occupants,
                    include_media=include_media,
                    include_graph=include_graph,
                )

            except Exception as e:
                self.display_geometry_in_exception(e)

                raise e
            self.changes_label.setText(f"Uploaded venues")

    def revert_button_clicked(self) -> None:
        self.set_update_sync_settings()
        # TODO: MAKE INTO A RELOAD INSTEAD?
        with InjectedProgressBar(parent=self.iface.mainWindow().statusBar()) as bar:
            self.changes_label.setText(f"Revert venues")
            try:
                revert_venues(
                    original_solution_venues=self.original_solution_venues,
                    settings=self.sync_module_settings,
                    progress_bar=bar,
                )
            except Exception as e:
                self.display_geometry_in_exception(e)

                raise e
            self.changes_label.setText(f"Reverted venues")

    def display_geometry_in_exception(self, e) -> None:
        # string_exception = "\n".join(e.args)

        string_exception = str(e)
        try:
            wkt_elements = list(zip(*extract_wkt_elements(string_exception)))
            if wkt_elements and len(wkt_elements) == 2:
                contexts, elements = wkt_elements

                contexts = [clean_str(c) for c in contexts]

                add_shapely_layer(
                    self,
                    elements,
                    name="exceptions",
                    columns=[{"contexts": c} for c in contexts],
                    crs=f"EPSG:{ MI_EPSG_NUMBER }",
                )
        except:
            ...

        logger.error(string_exception)

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
