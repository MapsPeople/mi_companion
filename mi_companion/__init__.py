from .constants import *

__version__ = VERSION
__author__ = PLUGIN_AUTHOR


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .mi_companion_plugin import MapsIndoorsCompanionPlugin

    from jord.qgis_utilities.helpers.logging import setup_logger
    import logging

    # setup_logger("Qgis") # For all of qgis
    logger: logging.Logger = setup_logger(
        __name__,
        logger_level=logging.INFO,
    )

    logger.debug(f"Setup {logger.name=}")
    logger.debug(
        f"Setup {setup_logger('integration_system', logger_level=logging.INFO).name=}"
    )

    return MapsIndoorsCompanionPlugin(iface)
