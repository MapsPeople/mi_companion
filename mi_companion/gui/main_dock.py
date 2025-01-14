import logging
import math
import os
from collections import defaultdict
from typing import Any, Optional

from jord.qgis_utilities import read_plugin_setting
from jord.qgis_utilities.helpers import InjectedProgressBar, signals
from jord.qlive_utilities import add_shapely_layer
from jord.qt_utilities import DockWidgetAreaFlag

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

# noinspection PyUnresolvedReferences
from qgis.gui import QgsDockWidget
from warg import get_submodules_by_path, reload_module

from integration_system.config import MapsIndoors, Settings, set_settings
from integration_system.mi import SolutionDepth, get_venue_key_mi_venue_map
from mi_companion.mi_editor import (
    layer_hierarchy_to_solution,
    revert_venues,
    solution_venue_to_layer_hierarchy,
)
from .gui_utilities import clean_str
from .make_solution_right_click import add_augmented_actions
from ..configuration.options import read_bool_setting
from ..constants import (
    DEFAULT_PLUGIN_SETTINGS,
    MI_EPSG_NUMBER,
    PLUGIN_REPOSITORY,
    PROJECT_NAME,
    VERSION,
)
from ..qgis_utilities import extract_wkt_elements, get_icon_path, resolve_path

FORM_CLASS, _ = uic.loadUiType(resolve_path("main_dock.ui", __file__))

signals.IS_DEBUGGING = True
logger = logging.getLogger(__name__)
VERBOSE = False

from pathlib import Path

from warg import ensure_in_sys_path

ensure_in_sys_path(Path(__file__).parent.parent)


class MapsIndoorsCompanionDockWidget(QgsDockWidget, FORM_CLASS):
    plugin_closing = pyqtSignal()

    def entry_point_wrapper(self, k, a: callable):
        def f():
            if k not in self.entry_point_instances:
                self.entry_point_instances[k] = a()

            if isinstance(self.entry_point_instances[k], QtWidgets.QDialog):
                self.entry_point_instances[k].show()
            elif isinstance(self.entry_point_instances[k], QtWidgets.QDockWidget):
                if False:
                    try:
                        self.iface_.mainWindow().removeDockWidget(
                            self.entry_point_instances[k]
                        )
                    except Exception as e:
                        logger.exception(e)

                self.iface_.mainWindow().addDockWidget(
                    DockWidgetAreaFlag.left.value,
                    self.entry_point_instances[k],
                )
                self.entry_point_instances[k].show()
                # self.entry_point_instances[k].setUserVisible(True)

            else:
                ...

        return f

    def upgrade_clicked(self, *_) -> None:
        # noinspection PyUnresolvedReferences
        import pyplugin_installer

        # noinspection PyUnresolvedReferences
        from qgis.PyQt.QtWidgets import (
            QMessageBox,
        )

        msg = f"Upgrading plugin to the latest version"
        QMessageBox.information(
            self.iface_.mainWindow(),
            msg,
            msg,
        )

        logger.error(msg)

        # shutil.rmtree(relative_bundled_packages_dir.absolute()) # TODO: IMPLEMENT!
        # shutil.rmtree(PLUGIN_DIR.absolute())

        # pyplugin_installer.instance().uninstallPlugin(PROJECT_NAME)
        # pyplugin_installer.installer_data.plugins.all().keys()
        reload = True
        pyplugin_installer.instance().fetchAvailablePlugins(reload)

        # pyplugin_installer.instance().installPlugin(PROJECT_NAME)

    def __init__(self, iface_: Any, parent: Optional[Any] = None):
        """Constructor."""
        super().__init__(parent)

        from integration_system.config import Settings

        # INITIALISATION OF ATTRS
        self.fetched_solution = None
        self.venue_name_id_map = None
        self.venues = None
        self.solution_external_id = None
        self.external_id_map = None
        #

        self.iface_ = iface_
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

        self.version_label.setText(f'<a href="{PLUGIN_REPOSITORY}">{VERSION}</a>')
        self.version_label.setOpenExternalLinks(False)
        signals.reconnect_signal(self.version_label.linkActivated, self.upgrade_clicked)

        # self.plugin_status_label.setText(plugin_version.plugin_status(PROJECT_NAME))

        self.changes_label.setText("")
        if False:
            self.sync_button.setEnabled(False)
            self.upload_button.setEnabled(False)

        self.original_solution_venues = defaultdict(dict)

        signals.reconnect_signal(
            self.solution_reload_button.clicked, self.refresh_solution_combo_box
        )
        if False:
            signals.reconnect_signal(
                self.solution_combo_box.lineEdit().editingFinished,
                self.refresh_solution_combo_box,
            )

        signals.reconnect_signal(
            self.venue_reload_button.clicked, self.refresh_venue_button_clicked
        )
        if False:
            signals.reconnect_signal(
                self.venue_combo_box.lineEdit().editingFinished,
                self.refresh_venue_button_clicked,
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

        self.import_dialog = None
        signals.reconnect_signal(self.import_button.clicked, self.import_button_clicked)

        self.export_dialog = None
        signals.reconnect_signal(self.export_button.clicked, self.export_button_clicked)

        self.solution_depth_combo_box = None
        if read_bool_setting("ADVANCED_MODE"):
            if False:
                self.sync_layout.addWidget(self.solution_depth_combo_box)

        entry_point_modules = get_submodules_by_path(
            Path(__file__).parent.parent / "entry_points"
        )

        self.entry_point_instances = {}
        self.entry_point_definitions = {
            getattr(d, "ENTRY_POINT_NAME"): self.entry_point_wrapper(
                getattr(d, "ENTRY_POINT_NAME"), getattr(d, "ENTRY_POINT_DIALOG")
            )
            for d in entry_point_modules
            if hasattr(d, "ENTRY_POINT_NAME")
        }

        if False:
            assert len(self.entry_point_definitions) == len(entry_point_modules), (
                f"{len(self.entry_point_definitions)=} {len(entry_point_modules)=} are not the same length, "
                f"probably there are duplicate ENTRY_POINT_DIALOG"
            )

        self.repopulate_grid_layout()

        signals.reconnect_signal(iface_.mapCanvas().mapToolSet, add_augmented_actions)

    def export_button_clicked(self):
        from .dialogs.solution_export import ENTRY_POINT_DIALOG as export_dialog

        if self.export_dialog is None:
            self.export_dialog = export_dialog()
        self.export_dialog.show()

    def import_button_clicked(self):
        from .dialogs.solution_import import ENTRY_POINT_DIALOG as import_dialog

        if self.import_dialog is None:
            self.import_dialog = import_dialog()
        self.import_dialog.show()

    def set_update_sync_settings(self):
        self.sync_module_settings = Settings(
            mapsindoors=MapsIndoors(
                username=read_plugin_setting(
                    "MAPS_INDOORS_USERNAME",
                    default_value=DEFAULT_PLUGIN_SETTINGS["MAPS_INDOORS_USERNAME"],
                    project_name=PROJECT_NAME,
                ),
                password=read_plugin_setting(
                    "MAPS_INDOORS_PASSWORD",
                    default_value=DEFAULT_PLUGIN_SETTINGS["MAPS_INDOORS_PASSWORD"],
                    project_name=PROJECT_NAME,
                ),
                token_endpoint=read_plugin_setting(
                    "MAPS_INDOORS_TOKEN_ENDPOINT",
                    default_value=DEFAULT_PLUGIN_SETTINGS[
                        "MAPS_INDOORS_TOKEN_ENDPOINT"
                    ],
                    project_name=PROJECT_NAME,
                ),
                manager_api_host=read_plugin_setting(
                    "MAPS_INDOORS_MANAGER_API_HOST",
                    default_value=DEFAULT_PLUGIN_SETTINGS[
                        "MAPS_INDOORS_MANAGER_API_HOST"
                    ],
                    project_name=PROJECT_NAME,
                ),
                media_api_host=read_plugin_setting(
                    "MAPS_INDOORS_MEDIA_API_HOST",
                    default_value=DEFAULT_PLUGIN_SETTINGS[
                        "MAPS_INDOORS_MEDIA_API_HOST"
                    ],
                    project_name=PROJECT_NAME,
                ),
            )
        )

        set_settings(self.sync_module_settings)

    def refresh_solution_combo_box(self, reload_venues: bool = True) -> None:
        from integration_system.mi import get_solution_name_external_id_map

        with InjectedProgressBar(
            parent=self.iface_.mainWindow().statusBar()
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
            self.external_id_map = get_solution_name_external_id_map()

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

        with InjectedProgressBar(parent=self.iface_.mainWindow().statusBar()) as bar:
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

            solution_id = get_solution_id(self.solution_external_id)
            if solution_id is None:
                logger.error(
                    f"Could not find solution id for {self.solution_external_id}"
                )
                return
            bar.setValue(30)

            self.venues = get_venue_key_mi_venue_map(
                solution_id,
            )

            bar.setValue(90)

            self.venue_name_id_map = {
                next(iter(v.venueInfo))["name"]: k for k, v in self.venues.items()
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

        solution_depth = SolutionDepth.obstacles

        if self.solution_depth_combo_box:
            solution_depth = str(self.solution_combo_box.currentText())

        include_route_elements = read_bool_setting("ADD_ROUTE_ELEMENTS")
        include_graph = read_bool_setting("ADD_GRAPH")

        include_occupants = False
        include_media = False

        with InjectedProgressBar(parent=self.iface_.mainWindow().statusBar()) as bar:
            if venue_name.strip() == "":  # TODO: Not supported ATM
                venues = list(self.venue_name_id_map.values())
                num_venues = float(len(venues))
                for i, v in enumerate(venues):
                    with InjectedProgressBar(
                        parent=self.iface_.mainWindow().statusBar()
                    ) as venue_bar:
                        (
                            self.original_solution_venues[self.solution_external_id][v]
                        ) = solution_venue_to_layer_hierarchy(
                            self,
                            self.solution_external_id,
                            v,
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
                        progress_bar=bar,
                        depth=solution_depth,
                        include_route_elements=include_route_elements,
                        include_occupants=include_occupants,
                        include_media=include_media,
                        include_graph=include_graph,
                    )
                    self.changes_label.setText(f"Downloaded {venue_name}")
                else:
                    logger.warning(f"Venue {venue_name} not found")

    def upload_button_clicked(self) -> None:
        self.set_update_sync_settings()

        solution_depth = SolutionDepth.obstacles
        if self.solution_depth_combo_box:
            solution_depth = str(self.solution_combo_box.currentText())

        include_occupants = False
        include_media = False

        include_route_elements = read_bool_setting("ADD_ROUTE_ELEMENTS")
        include_graph = read_bool_setting("ADD_GRAPH")

        with InjectedProgressBar(parent=self.iface_.mainWindow().statusBar()) as bar:
            self.changes_label.setText(f"Uploading venues")
            try:
                layer_hierarchy_to_solution(
                    self,
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
        with InjectedProgressBar(parent=self.iface_.mainWindow().statusBar()) as bar:
            self.changes_label.setText(f"Revert venues")
            try:
                revert_venues(
                    original_solution_venues=self.original_solution_venues,
                    progress_bar=bar,
                )
            except Exception as e:
                self.display_geometry_in_exception(e)

                raise e
            self.changes_label.setText(f"Reverted venues")

    def display_geometry_in_exception(self, e) -> None:
        # string_exception = "\n".join(e.args)

        string_exception = str(e)
        if False:
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
                        crs=f"EPSG:{MI_EPSG_NUMBER}",
                    )
            except Exception:
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
        for i, (k, entry_callable_definition) in enumerate(
            self.entry_point_definitions.items()
        ):
            button = QtWidgets.QPushButton(k)

            signals.reconnect_signal(button.clicked, entry_callable_definition)

            self.entry_point_grid.addWidget(
                button, math.floor(i / num_columns), i % num_columns
            )

    # noinspection PyPep8Naming
    def closeEvent(self, event) -> None:  # pylint: disable=invalid-name
        self.plugin_closing.emit()
        event.accept()
