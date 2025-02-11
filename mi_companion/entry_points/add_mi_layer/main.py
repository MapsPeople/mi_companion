#!/usr/bin/python
import logging

logger = logging.getLogger(__name__)

# noinspection PyUnresolvedReferences
from qgis.core import (
    QgsProject,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    Qgis,
)


def run() -> None:
    """
    Add an MI layer to the project

    """

    # noinspection PyUnresolvedReferences
    from qgis.utils import iface

    ...
