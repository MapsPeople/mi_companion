#!/usr/bin/python
import logging
from pathlib import Path

import ifcopenshell

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

# noinspection PyUnresolvedReferences
from qgis.utils import iface

from jord.qgis_utilities.helpers import InjectedProgressBar
from mi_companion import RESOURCE_BASE_PATH
from mi_companion.layer_descriptors import DATABASE_GROUP_DESCRIPTOR
from mi_companion.mi_editor.conversion import add_solution_layers

logger = logging.getLogger(RESOURCE_BASE_PATH)
__all__ = []


def load_ifc(file_path: Path) -> ifcopenshell.entity_instance:
    return ifcopenshell.open(file_path)


def ifc_to_mi_solution(ifc_model):
    """


    :param ifc_model:
    :return:
    """
    return None


def run(*, ifc_zip_file_path: Path) -> None:
    """
    Does nothing yet.

    :param ifc_zip_file_path:
    :return:
    """
    qgis_instance_handle = QgsProject.instance()
    layer_tree_root = QgsProject.instance().layerTreeRoot()

    ifc_model = load_ifc(ifc_zip_file_path)

    mi_solution = ifc_to_mi_solution(ifc_model)

    with InjectedProgressBar(parent=iface.mainWindow().statusBar()) as progress_bar:
        add_solution_layers(
            qgis_instance_handle=qgis_instance_handle,
            solution=mi_solution,
            layer_tree_root=layer_tree_root,
            mi_hierarchy_group_name=DATABASE_GROUP_DESCRIPTOR,
            progress_bar=progress_bar,
        )
