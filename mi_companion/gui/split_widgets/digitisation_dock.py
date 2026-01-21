from pathlib import Path

from jord.qt_utilities import DockWidgetAreaFlag
from warg import ensure_in_sys_path, first, get_submodules_by_path
from ... import entry_points
from ...entry_points import (
    add_language_to_group,
    assign_value_to_dimension,
    caddy_import,
    duplicate_group,
    imdf_import,
    regen_field,
    svg_import,
    transform_group,
    validate_hierarchy,
)


ensure_in_sys_path(Path(__file__).parent.parent)
import logging
from typing import Any, Callable, Optional

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtGui, QtWidgets, uic, QtCore

# noinspection PyUnresolvedReferences
from qgis.gui import QgsDockWidget

from jord.qgis_utilities import (
    InjectedProgressBar,
    duplicate_groups,
    read_plugin_setting,
    signals,
)
from jord.qlive_utilities import add_shapely_layer
from mi_companion.mi_editor import (
    layer_hierarchy_to_solution,
)
from sync_module.mi import SolutionDepth
from sync_module.mi.config import MapsIndoors, Settings, set_settings
from sync_module.mi_sync_constants import MI_EPSG_NUMBER
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
from ...constants import (
    DEFAULT_PLUGIN_SETTINGS,
    PLUGIN_DIR,
    PROJECT_NAME,
)


__all__ = ["DigitisationWidget"]


class DigitisationWidget(
    QgsDockWidget,
    first(uic.loadUiType(str(resolve_path("digitisation_dock_widget.ui", __file__)))),
):
    plugin_closing = QtCore.pyqtSignal()
    menu_name = "Digitisation"

    def __init__(self, iface_: Any, parent: Optional[Any] = None):
        super().__init__(parent)

        self.setupUi(self)

        self.iface_ = iface_
        self.entry_point_instances = {}
        self._populate_layouts()

    def entry_point_wrapper(self, k: str, a: Callable) -> Callable:
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
                        _logger.exception(e)

                self.iface_.mainWindow().addDockWidget(
                    DockWidgetAreaFlag.left.value,
                    self.entry_point_instances[k],
                )
                self.entry_point_instances[k].show()
            else:
                ...

        return f

    def _populate_layouts(self):

        for i in (svg_import, caddy_import, imdf_import):
            button = QtWidgets.QPushButton(i.ENTRY_POINT_NAME)
            signals.reconnect_signal(
                button.clicked,
                self.entry_point_wrapper(i.ENTRY_POINT_NAME, i.ENTRY_POINT_DIALOG),
            )
            self.importers_layout.addWidget(button)

        for i in (duplicate_group, add_language_to_group, regen_field):
            button = QtWidgets.QPushButton(i.ENTRY_POINT_NAME)
            signals.reconnect_signal(
                button.clicked,
                self.entry_point_wrapper(i.ENTRY_POINT_NAME, i.ENTRY_POINT_DIALOG),
            )
            self.hierarchy_layout.addWidget(button)

        for i in (transform_group, assign_value_to_dimension):
            button = QtWidgets.QPushButton(i.ENTRY_POINT_NAME)
            signals.reconnect_signal(
                button.clicked,
                self.entry_point_wrapper(i.ENTRY_POINT_NAME, i.ENTRY_POINT_DIALOG),
            )
            self.transformation_layout.addWidget(button)
