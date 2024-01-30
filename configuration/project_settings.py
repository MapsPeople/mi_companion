from jord.qt_utilities import DockWidgetAreaFlag

from .. import PROJECT_NAME

DEFAULT_PROJECT_SETTINGS = {
    "RESOURCES_BASE_PATH": f":/{PROJECT_NAME.lower().replace(' ', '_')}",
    "DEFAULT_WIDGET_AREA": DockWidgetAreaFlag.right,
    "NUM_COLUMNS": 3,
    "MAPS_INDOORS_PASSWORD": "REPLACE_ME",
    "MAPS_INDOORS_USERNAME": "REPLACE_ME@mapspeople.com",
    "MAPS_INDOORS_INTEGRATION_API_HOST": "https://integration-automation.mapsindoors.com",
    "MAPS_INDOORS_TOKEN_ENDPOINT": "https://auth.mapsindoors.com/connect/token",
    "MAPS_INDOORS_MANAGER_API_HOST": "https://v2.mapsindoors.com",
}
