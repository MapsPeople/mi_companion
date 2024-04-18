from jord.qt_utilities import DockWidgetAreaFlag

from .. import PROJECT_NAME

DEFAULT_PLUGIN_SETTINGS = {
    "RESOURCES_BASE_PATH": f":/{PROJECT_NAME.lower().replace(' ', '_')}",
    "DEFAULT_WIDGET_AREA": DockWidgetAreaFlag.right,
    "NUM_COLUMNS": 3,
    "MAPS_INDOORS_PASSWORD": "REPLACE_ME",  # TODO: LOOK INTO GOOGLE AUTHENTICATION
    "MAPS_INDOORS_USERNAME": "REPLACE_ME@mapspeople.com",  # TODO: LOOK INTO GOOGLE AUTHENTICATION
    "MAPS_INDOORS_TOKEN_ENDPOINT": "https://auth.mapsindoors.com/connect/token",
    "MAPS_INDOORS_MANAGER_API_HOST": "https://v2.mapsindoors.com",
    "MAPS_INDOORS_MEDIA_API_HOST": "https://media.mapsindoors.com",
    "MAPS_INDOORS_MANAGER_API_TOKEN": None,
    "MAPS_INDOORS_INTEGRATION_API_TOKEN": None,
    "ALLOW_LOCATION_TYPE_CREATION": False,
    "GENERATE_MISSING_EXTERNAL_IDS": False,
    "REQUIRE_MINIMUM_FLOOR": True,
    "ALLOW_SOLUTION_CREATION": False,
    "AWAIT_CONFIRMATION": True,
    "ADVANCED_MODE": False,
}
