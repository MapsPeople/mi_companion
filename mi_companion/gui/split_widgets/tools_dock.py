from pathlib import Path

import logging
import math

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtGui, QtWidgets, uic

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import pyqtSignal

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtWidgets import (
    QMessageBox,
)

# noinspection PyUnresolvedReferences
from qgis.core import (
    QgsProject,
)

# noinspection PyUnresolvedReferences
from qgis.gui import QgsDockWidget
from typing import Any, Callable, Optional

from jord.qgis_utilities import read_plugin_setting
from jord.qgis_utilities.helpers import signals
from jord.qt_utilities import DockWidgetAreaFlag
from mi_companion.entry_points.add_language_to_group import (
    ENTRY_POINT_NAME as ADD_LANGUAGE_BUTTON_NAME,
)
from warg import ensure_in_sys_path, get_submodules_by_path
from ...configuration.options import read_bool_setting
from ...constants import (
    DEFAULT_PLUGIN_SETTINGS,
    PROJECT_NAME,
)

ensure_in_sys_path(Path(__file__).parent.parent)
_logger = logging.getLogger(__name__)


class EntryPointsWidget(QgsDockWidget):
    plugin_closing = pyqtSignal()
    menu_name = "Tools"

    def __init__(self, iface_: Any, parent: Optional[Any] = None):
        super().__init__(parent)
        self.iface_ = iface_
        self.entry_point_instances = {}
        self.entry_point_definitions = {}

        # Create a container widget to hold the layout
        self.container_widget = QtWidgets.QWidget()
        self.grid_layout = QtWidgets.QGridLayout()
        self.container_widget.setLayout(self.grid_layout)

        # Set the container as the visual content of the DockWidget
        self.setWidget(self.container_widget)

        self._load_entry_points()
        self._populate_grid()

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

    def _load_entry_points(self):
        entry_point_modules = get_submodules_by_path(
            Path(__file__).parent.parent.parent / "entry_points"
        )

        self.entry_point_definitions = {
            getattr(d, "ENTRY_POINT_NAME"): self.entry_point_wrapper(
                getattr(d, "ENTRY_POINT_NAME"), getattr(d, "ENTRY_POINT_DIALOG")
            )
            for d in entry_point_modules
            if hasattr(d, "ENTRY_POINT_NAME")
        }

        if not read_bool_setting("ADD_LANGUAGE_BUTTON"):
            if ADD_LANGUAGE_BUTTON_NAME in self.entry_point_definitions:
                self.entry_point_definitions.pop(ADD_LANGUAGE_BUTTON_NAME)
                _logger.warning(
                    f"Removed '{ADD_LANGUAGE_BUTTON_NAME}'-button from entry_point_definitions"
                )

    def _populate_grid(self):
        # Clear existing
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

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
            self.grid_layout.addWidget(
                button, math.floor(i / num_columns), i % num_columns
            )
