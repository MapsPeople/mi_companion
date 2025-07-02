#!/usr/bin/python
import logging
from pathlib import Path

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

# noinspection PyUnresolvedReferences
from qgis.utils import iface

from mi_companion import RESOURCE_BASE_PATH

logger = logging.getLogger(RESOURCE_BASE_PATH)
__all__ = ["run"]


def run(*, imdf_zip_file_path: Path) -> None:
    """

    :param imdf_zip_file_path:
    :return:
    """
    from mi_companion.layer_descriptors import DATABASE_GROUP_DESCRIPTOR
    from mi_companion.mi_editor.conversion import add_solution_layers
    from jord.qgis_utilities.helpers import InjectedProgressBar
    from midf.conversion import to_mi_solution
    from midf.linking import link_imdf
    from midf.loading import load_imdf

    qgis_instance_handle = QgsProject.instance()
    layer_tree_root = QgsProject.instance().layerTreeRoot()

    if isinstance(imdf_zip_file_path, str):
        imdf_zip_file_path = Path(imdf_zip_file_path)

    imdf_dict = load_imdf(imdf_zip_file_path)

    midf_solution = link_imdf(imdf_dict)

    mi_solution = to_mi_solution(midf_solution)

    with InjectedProgressBar(parent=iface.mainWindow().statusBar()) as progress_bar:
        add_solution_layers(
            qgis_instance_handle=qgis_instance_handle,
            solution=mi_solution,
            layer_tree_root=layer_tree_root,
            mi_hierarchy_group_name=DATABASE_GROUP_DESCRIPTOR,
            progress_bar=progress_bar,
        )
