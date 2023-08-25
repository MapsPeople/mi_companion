# -*- coding: utf-8 -*-

from .constants import *

__version__ = VERSION
__author__ = PLUGIN_AUTHOR


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load ProfileCreator class from file ProfileCreator.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .gds_companion import GdsCompanion

    return GdsCompanion(iface)
