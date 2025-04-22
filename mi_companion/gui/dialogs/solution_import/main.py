#!/usr/bin/python
import logging
from pathlib import Path

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

# noinspection PyUnresolvedReferences
from qgis.utils import iface

logger = logging.getLogger(__name__)


def run(*, path: Path) -> None:
    from jord.qgis_utilities.helpers import InjectedProgressBar

    from integration_system.json_serde import from_json
    from mi_companion.layer_descriptors import DATABASE_GROUP_DESCRIPTOR
    from mi_companion.mi_editor.conversion import add_solution_layers

    qgis_instance_handle = QgsProject.instance()
    layer_tree_root = QgsProject.instance().layerTreeRoot()

    if not isinstance(path, Path):
        path = Path(path)

    with open(path) as f:
        solution = from_json(f.read())

    with InjectedProgressBar(parent=iface.mainWindow().statusBar()) as progress_bar:
        add_solution_layers(
            qgis_instance_handle=qgis_instance_handle,
            solution=solution,
            layer_tree_root=layer_tree_root,
            mi_hierarchy_group_name=DATABASE_GROUP_DESCRIPTOR,
            progress_bar=progress_bar,
        )
