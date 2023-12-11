from jord.qt_utilities import DockWidgetAreaFlag

from .. import PROJECT_NAME

DEFAULT_PROJECT_SETTINGS = {
    "RESOURCES_BASE_PATH": f":/{PROJECT_NAME.lower().replace(' ', '_')}",
    "DEFAULT_WIDGET_AREA": DockWidgetAreaFlag.right,
    "NUM_COLUMNS": 3,
}
