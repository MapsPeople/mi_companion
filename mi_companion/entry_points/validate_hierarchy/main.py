#!/usr/bin/python
import logging

# noinspection PyUnresolvedReferences
# noinspection PyUnresolvedReferences
from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsProject,
    QgsProject,
)

# noinspection PyUnresolvedReferences
from qgis.utils import iface

from jord.qgis_utilities.helpers import InjectedProgressBar
from mi_companion import RESOURCE_BASE_PATH

logger = logging.getLogger(RESOURCE_BASE_PATH)
__all__ = ["run"]


def run() -> None:
    """
    Validate the hierarchy of the solution layers.
    """

    from mi_companion.mi_editor import convert_solution_layers_to_solution
    from mi_companion.layer_descriptors import DATABASE_GROUP_DESCRIPTOR

    qgis_instance_handle = QgsProject.instance()

    layer_tree_root = QgsProject.instance().layerTreeRoot()

    mi_group = layer_tree_root.findGroup(DATABASE_GROUP_DESCRIPTOR)

    with InjectedProgressBar(parent=iface.mainWindow().statusBar()) as progress_bar:
        solutions = convert_solution_layers_to_solution(
            qgis_instance_handle,
            progress_bar=progress_bar,
            mi_group=mi_group,
            upload_venues=False,
            collect_invalid=True,
        )
