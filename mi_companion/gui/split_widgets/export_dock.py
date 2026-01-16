import logging
import math
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Optional

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

from jord.qgis_utilities import InjectedProgressBar, read_plugin_setting, signals
from jord.qlive_utilities import add_shapely_layer
from jord.qt_utilities import DockWidgetAreaFlag
from mi_companion.entry_points.add_language_to_group import (
    ENTRY_POINT_NAME as ADD_LANGUAGE_BUTTON_NAME,
)
from mi_companion.mi_editor import (
    layer_hierarchy_to_solution,
    revert_venues,
    solution_venue_to_layer_hierarchy,
)
from mi_companion.mi_editor.hierarchy.hierarchy_validation import (
    add_solution_hierarchy_change_listener,
    remove_solution_hierarchy_change_listener,
)
from sync_module.mi import SolutionDepth, get_venue_key_mi_venue_map
from sync_module.mi.config import MapsIndoors, Settings, set_settings
from sync_module.mi_sync_constants import MI_EPSG_NUMBER
from warg import get_submodules_by_path, reload_module, ensure_in_sys_path
from ..gui_utilities import clean_str
from ..make_solution_right_click import add_augmented_actions
from ...configuration.options import read_bool_setting
from ...constants import (
    DEFAULT_PLUGIN_SETTINGS,
    PLUGIN_REPOSITORY,
    PROJECT_NAME,
    VERSION,
)
from ...qgis_utilities import extract_wkt_elements, get_icon_path, resolve_path
from ...qgis_utilities.creation_mode import (
    put_location_layers_into_creation_mode,
)

ensure_in_sys_path(Path(__file__).parent.parent)

FORM_CLASS, _ = uic.loadUiType(resolve_path("main_dock.ui", __file__))

signals.IS_DEBUGGING = True
logger = logging.getLogger(__name__)
VERBOSE = False
