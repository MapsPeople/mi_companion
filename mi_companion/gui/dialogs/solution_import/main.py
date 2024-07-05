#!/usr/bin/python


def run(*, path: str) -> None:
    import logging

    logger = logging.getLogger(__name__)

    # noinspection PyUnresolvedReferences
    from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject
    from qgis.utils import iface
    from jord.qgis_utilities.helpers import InjectedProgressBar

    from integration_system.json_serde import from_json
    from mi_companion.configuration.constants import MI_HIERARCHY_GROUP_NAME
    from mi_companion.mi_editor.conversion import add_solution_layers

    qgis_instance_handle = QgsProject.instance()
    layer_tree_root = QgsProject.instance().layerTreeRoot()

    with open(path) as f:
        solution = from_json(f.read())

    with InjectedProgressBar(parent=iface.mainWindow().statusBar()) as progress_bar:
        add_solution_layers(
            qgis_instance_handle=qgis_instance_handle,
            solution=solution,
            layer_tree_root=layer_tree_root,
            mi_hierarchy_group_name=MI_HIERARCHY_GROUP_NAME,
            progress_bar=progress_bar,
        )
