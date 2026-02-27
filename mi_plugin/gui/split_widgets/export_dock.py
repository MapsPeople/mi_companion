from pathlib import Path

from warg import ensure_in_sys_path, first

ensure_in_sys_path(Path(__file__).parent.parent)
import logging
from typing import Any, Optional


from qgis.PyQt import uic, QtCore


from qgis.gui import QgsDockWidget

from jord.qgis_utilities import InjectedProgressBar, read_plugin_setting, signals
from jord.qlive_utilities import add_shapely_layer
from mi_plugin.mi_editor import (
    layer_hierarchy_to_solution,
)
from sync_module.mi import SolutionDepth
from sync_module.mi.config import MapsIndoors, Settings, set_settings
from sync_module.constants import MI_EPSG_NUMBER
from ..gui_utilities import clean_str
from ...constants import (
    DEFAULT_PLUGIN_SETTINGS,
    PROJECT_NAME,
)
from ...mi_editor.authentication.get_credentials_from_auth_manager import (
    get_credentials_from_auth_manager,
)
from ...qgis_utilities import extract_wkt_elements, resolve_path

signals.IS_DEBUGGING = True
_logger = logging.getLogger(__name__)
VERBOSE = False

__all__ = ["ExportWidget"]


class ExportWidget(
    QgsDockWidget,
    first(uic.loadUiType(str(resolve_path("export_dock_widget.ui", __file__)))),
):
    plugin_closing = QtCore.pyqtSignal()
    menu_name = "Export"

    def __init__(self, iface_: Any, parent: Optional[Any] = None):
        super().__init__(parent)

        self.setupUi(self)

        self.iface_ = iface_

        from sync_module.mi.config import Settings

        self.sync_module_settings = Settings()

        self.export_dialog = None

        for s, c in (
            (self.export_button.clicked, self.export_button_clicked),
            (self.upload_button.clicked, self.upload_button_clicked),
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

    def export_button_clicked(self):
        from ..dialogs.solution_export import ENTRY_POINT_DIALOG as export_dialog

        if self.export_dialog is None:  #
            self.export_dialog = export_dialog()
        self.export_dialog.show()

    def upload_button_clicked(self) -> None:
        self.set_update_sync_settings()

        solution_depth = SolutionDepth.obstacles

        with InjectedProgressBar(parent=self.iface_.mainWindow().statusBar()) as bar:

            try:
                layer_hierarchy_to_solution(
                    self,
                    progress_bar=bar,
                    solution_depth=solution_depth,
                )

            except Exception as e:
                self.display_geometry_in_exception(e)

                raise e

    # noinspection PyPep8Naming
    def closeEvent(self, event: Any) -> None:  # pylint: disable=invalid-name
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
