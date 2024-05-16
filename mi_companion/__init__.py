import logging


from .constants import *

__version__ = VERSION
__author__ = PLUGIN_AUTHOR


from jord.qt_utilities import DockWidgetAreaFlag

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
    "GENERATE_MISSING_EXTERNAL_IDS": True,
    "REQUIRE_MINIMUM_FLOOR": True,
    "ALLOW_SOLUTION_CREATION": False,
    "AWAIT_CONFIRMATION": True,
    "ADVANCED_MODE": False,
    "ADD_GRAPH": True,
    "ADD_DOORS": True,
    "SYNC_GRAPH_AND_ROUTE_ELEMENTS": False,
    "ONLY_SHOW_FIRST_FLOOR": True,
    "CONFIRMATION_DIALOG_ENABLED": True,
    "MAKE_HIGHWAY_TYPE_DROPDOWN": True,
    "MAKE_LOCATION_TYPE_DROPDOWN": True,
    "MAKE_DOOR_TYPE_DROPDOWN": True,
    "MAKE_VENUE_TYPE_DROPDOWN": True,
    "SHOW_GRAPH_ON_LOAD": False,
    "POST_FIT_FLOORS": False,
    "POST_FIT_BUILDINGS": False,
    "POST_FIT_VENUES": False,
    "OPERATION_PROGRESS_BAR_ENABLED": True,
    "SOLVING_PROGRESS_BAR_ENABLED": True,
    "LOGGING_LEVEL": logging.WARNING,
    "REPROJECT_SHAPES": False,
}


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .mi_companion_plugin import MapsIndoorsCompanionPlugin

    from jord.qgis_utilities import read_plugin_setting
    from jord.qgis_utilities.helpers.logging import add_logging_handler_once

    ADD_SENTRY_LOGGER = False
    if ADD_SENTRY_LOGGER:
        try:
            from sentry_sdk import init
            from sentry_sdk.integrations.logging import (
                LoggingIntegration,
                EventHandler,
                BreadcrumbHandler,
            )  # I hate this interface!

            init(
                dsn="https://0d5b385b29467264d1f54f67318b1c52@o351128.ingest.us.sentry.io/4507175970996224",
                # Set traces_sample_rate to 1.0 to capture 100%
                # of transactions for performance monitoring.
                traces_sample_rate=1.0,
                # default_integrations=True,
                integrations=[LoggingIntegration(event_level=None, level=None)],
                # integrations=[
                #    sentry_sdk.integrations.LoggingIntegration(
                #        level=logging.INFO,  # Capture info and above as breadcrumbs
                #        event_level=logging.INFO,  # Send records as events
                #    ),
                # ],
            )

        except Exception:
            ...

    try:
        from jord.qgis_utilities.helpers.logging import setup_logger
        import logging

        logging_level = read_plugin_setting(
            "LOGGING_LEVEL",
            default_value=DEFAULT_PLUGIN_SETTINGS["LOGGING_LEVEL"],
            project_name=PROJECT_NAME,
        )

        logger: logging.Logger = setup_logger(
            __name__,
            logger_level=logging_level,
        )

        if ADD_SENTRY_LOGGER:
            try:
                import sentry_sdk

                add_logging_handler_once(
                    logger, sentry_sdk.integrations.logging.EventHandler(level=0)
                )
                add_logging_handler_once(
                    logger, sentry_sdk.integrations.logging.BreadcrumbHandler(level=0)
                )
            except Exception:
                ...

        logger.debug(f"Setup {logger.name=}")
        logger.debug(
            f"Setup {setup_logger('svaguely', logger_level=logging_level).name=}"
        )
        logger.debug(f"Setup {setup_logger('jord', logger_level=logging_level).name=}")
        logger.debug(
            f"Setup {setup_logger('integration_system', logger_level=logging_level).name=}"
        )

    except Exception:
        ...

    return MapsIndoorsCompanionPlugin(iface)
