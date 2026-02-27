from pathlib import Path

from warg import ensure_in_sys_path, first

ensure_in_sys_path(Path(__file__).parent.parent)

from collections import defaultdict

from jord.qgis_utilities import InjectedProgressBar
from jord.qlive_utilities import add_shapely_layer
from mi_plugin.mi_editor import (
    revert_venues,
    solution_venue_to_layer_hierarchy,
)
from mi_plugin.mi_editor.hierarchy.hierarchy_validation import (
    add_solution_hierarchy_change_listener,
    remove_solution_hierarchy_change_listener,
)
from sync_module.mi import SolutionDepth, get_venue_key_mi_venue_map
from sync_module.mi.config import MapsIndoors, set_settings
from sync_module.constants import MI_EPSG_NUMBER

from ..gui_utilities import clean_str
from ...mi_editor.authentication.get_credentials_from_auth_manager import (
    get_credentials_from_auth_manager,
)
from ...qgis_utilities import extract_wkt_elements, resolve_path

import logging


from qgis.PyQt import uic, QtCore


from qgis.gui import QgsDockWidget


from qgis.core import QgsProject

from typing import Any, Optional

from jord.qgis_utilities import read_plugin_setting
from jord.qgis_utilities.helpers import signals
from sync_module.mi.config import Settings
from ...configuration.options import read_bool_setting
from ...constants import (
    DEFAULT_PLUGIN_SETTINGS,
    PROJECT_NAME,
)

signals.IS_DEBUGGING = True

VERBOSE = False


_logger = logging.getLogger(__name__)


__all__ = ["ImportWidget"]


class ImportWidget(
    QgsDockWidget,
    first(uic.loadUiType(str(resolve_path("import_dock_widget.ui", __file__)))),
):
    plugin_closing = QtCore.pyqtSignal()
    menu_name = "Import"

    def __init__(self, iface_: Any, parent: Optional[Any] = None):
        super().__init__(parent)
        self.setupUi(self)

        self.iface_ = iface_
        self.qgis_project = QgsProject.instance()

        self.sync_module_settings = Settings()

        # INITIALISATION OF ATTRS
        self.fetched_solution = None
        self.venue_name_id_map = None
        self.venues = None
        self.solution_external_id = None
        self.external_id_map = None

        self.import_dialog = None

        add_solution_hierarchy_change_listener()

        self.original_solution_venues = defaultdict(dict)

        for s, c in (
            (self.import_button.clicked, self.import_button_clicked),
            (self.solution_reload_button.clicked, self.refresh_solution_combo_box),
            (self.venue_reload_button.clicked, self.refresh_venue_button_clicked),
            (self.solution_combo_box.currentIndexChanged, self.solution_combo_changed),
            (self.solution_combo_box.currentTextChanged, self.solution_combo_changed),
            (self.sync_button.clicked, self.download_button_clicked),
        ):
            signals.reconnect_signal(s, c)

    def set_update_sync_settings(self):
        mp_username, mp_password = get_credentials_from_auth_manager(self.iface_)

        self.sync_module_settings = Settings(
            mapsindoors=MapsIndoors(
                username=mp_username,
                password=mp_password,
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
                manager_api_timeout=read_plugin_setting(
                    "MAPS_INDOORS_MANAGER_API_TIMEOUT",
                    default_value=DEFAULT_PLUGIN_SETTINGS[
                        "MAPS_INDOORS_MANAGER_API_TIMEOUT"
                    ],
                    project_name=PROJECT_NAME,
                ),
                media_api_timeout=read_plugin_setting(
                    "MAPS_INDOORS_MEDIA_API_TIMEOUT",
                    default_value=DEFAULT_PLUGIN_SETTINGS[
                        "MAPS_INDOORS_MEDIA_API_TIMEOUT"
                    ],
                    project_name=PROJECT_NAME,
                ),
            )
        )

        set_settings(self.sync_module_settings)

    def refresh_solution_combo_box(self, reload_venues: bool = True) -> None:
        from sync_module.mi import get_solution_name_external_id_map

        with InjectedProgressBar(
            parent=self.iface_.mainWindow().statusBar()
        ) as bar:  # TODO: add a text label or format progress bar with a title
            bar.setValue(10)
            self.set_update_sync_settings()
            current_solution_name = str(self.solution_combo_box.currentText()).strip()
            _logger.debug(f"{current_solution_name=}")

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
        from sync_module.mi import (
            get_solution_id,
        )

        self.set_update_sync_settings()

        if self.external_id_map is None:
            self.refresh_solution_combo_box(reload_venues=False)

        with InjectedProgressBar(parent=self.iface_.mainWindow().statusBar()) as bar:
            current_selected_solution_name = str(self.solution_combo_box.currentText())

            if current_selected_solution_name not in self.external_id_map:
                _logger.error(
                    f"Could not find external_id for solution id for {self.solution_external_id}"
                )
                return

            self.solution_external_id = self.external_id_map[
                current_selected_solution_name
            ]
            bar.setValue(10)

            solution_id = get_solution_id(self.solution_external_id)
            if solution_id is None:
                _logger.error(
                    f"Could not find solution id for {self.solution_external_id}"
                )
                return
            bar.setValue(30)

            self.venues = get_venue_key_mi_venue_map(
                solution_id,
            )

            bar.setValue(90)

            solution_default_language = "en"

            self.venue_name_id_map = {}
            for k, v in self.venues.items():
                venue_info = None
                for vi in v.venueInfo:
                    if solution_default_language == vi.language:
                        venue_info = vi
                        break
                if venue_info:
                    venue_name = venue_info.name
                    if venue_name in self.venue_name_id_map:
                        _logger.warning(
                            f"Duplicate venue name found: {venue_name}. Using the latest one."
                        )
                        venue_name += f" ({k})"

                else:
                    venue_name = f"venue_id: {k}"

                self.venue_name_id_map[venue_name] = k

            self.venue_combo_box.clear()
            self.venue_combo_box.addItems(sorted(self.venue_name_id_map.keys()))

            bar.setValue(100)

    def import_button_clicked(self):
        from ..dialogs.solution_import import ENTRY_POINT_DIALOG as import_dialog

        if self.import_dialog is None:
            self.import_dialog = import_dialog()
        self.import_dialog.show()

    def download_button_clicked(self) -> None:
        venue_name = str(self.venue_combo_box.currentText())
        if venue_name.strip() == "":
            _logger.error(f"No venue was selected!")
            return

        with InjectedProgressBar(
            parent=self.iface_.mainWindow().statusBar()
        ) as download_bar:
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
                            depth=SolutionDepth.occupants,
                            include_occupants=read_bool_setting("ADD_OCCUPANTS"),
                            include_media=read_bool_setting("ADD_MEDIA"),
                        )
                    download_bar.setValue(int((float(i) / num_venues) * 100))

            else:
                if venue_name in self.venue_name_id_map:

                    (
                        self.original_solution_venues[self.solution_external_id][
                            venue_name
                        ]
                    ) = solution_venue_to_layer_hierarchy(
                        self,
                        self.solution_external_id,
                        self.venue_name_id_map[venue_name],
                        progress_bar=download_bar,
                        depth=SolutionDepth.occupants,
                        include_occupants=read_bool_setting("ADD_OCCUPANTS"),
                        include_media=read_bool_setting("ADD_MEDIA"),
                    )

                else:
                    _logger.warning(f"Venue {venue_name} not found")

    def revert_button_clicked(self) -> None:
        self.set_update_sync_settings()

        with InjectedProgressBar(parent=self.iface_.mainWindow().statusBar()) as bar:

            try:
                revert_venues(
                    original_solution_venues=self.original_solution_venues,
                    progress_bar=bar,
                )
            except Exception as e:
                self.display_geometry_in_exception(e)

                raise e

    # noinspection PyPep8Naming
    def closeEvent(self, event: Any) -> None:  # pylint: disable=invalid-name
        remove_solution_hierarchy_change_listener()

        self.plugin_closing.emit()
        event.accept()

    def display_geometry_in_exception(self, e: Exception) -> None:
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

        _logger.error(string_exception)
