from .constants import *

__version__ = VERSION
__author__ = PLUGIN_AUTHOR


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    logger = None
    #
    from .mi_companion_plugin import MapsIndoorsCompanionPlugin
    import logging
    from jord.qgis_utilities import (
        read_plugin_setting,
        add_logging_handler_once,
        setup_qgs_logger,
    )

    ADD_SENTRY_LOGGER = False

    if False:
        try:
            logging_level = read_plugin_setting(
                "LOGGING_LEVEL",
                default_value=DEFAULT_PLUGIN_SETTINGS["LOGGING_LEVEL"],
                project_name=PROJECT_NAME,
            )

            logger: logging.Logger = setup_qgs_logger(
                __name__,
                logger_level=logging_level,
            )
        except Exception as e:
            if logger:
                logger.error(f"{e}")

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

            except Exception as e:
                if logger:
                    logger.error(f"{e}")

    try:
        logging_level = read_plugin_setting(
            "LOGGING_LEVEL",
            default_value=DEFAULT_PLUGIN_SETTINGS["LOGGING_LEVEL"],
            project_name=PROJECT_NAME,
        )

        # sys.stdout = open(os.devnull, "w")
        # sys.stderr = open(os.devnull, "w")

        # sys.stdout = sys.__stdout__
        # sys.stderr = sys.__stderr__

        logger: logging.Logger = setup_qgs_logger(
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

        logger.error(f"Setup {logger.name=}, {logging_level=}")
        logger.debug(
            f"Setup {setup_qgs_logger('svaguely', logger_level=logging_level).name=}"
        )
        logger.debug(
            f"Setup {setup_qgs_logger('jord', logger_level=logging_level).name=}"
        )
        logger.debug(
            f"Setup {setup_qgs_logger('warg', logger_level=logging_level).name=}"
        )
        logger.debug(
            f"Setup {setup_qgs_logger('apppath', logger_level=logging_level).name=}"
        )
        logger.debug(
            f"Setup {setup_qgs_logger('caddy', logger_level=logging_level).name=}"
        )
        from sync_module.mi_sync_constants import PRODUCTION

        logger.error(
            f"Setup {setup_qgs_logger('sync_module', logger_level=logging_level).name=}, "
            f"{PRODUCTION=}"
        )

    except Exception as e:
        if logger:
            logger.error(f"{e}")

    return MapsIndoorsCompanionPlugin(iface)
