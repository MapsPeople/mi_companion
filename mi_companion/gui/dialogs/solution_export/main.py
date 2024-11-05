#!/usr/bin/python

import logging
from pathlib import Path

logger = logging.getLogger(__name__)
SERIALISED_SOLUTION_EXTENSION = ".json"


def run(*, path: Path) -> None:
    # noinspection PyUnresolvedReferences
    from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

    # noinspection PyUnresolvedReferences
    from qgis.utils import iface
    from jord.qgis_utilities.helpers import InjectedProgressBar

    from integration_system.json_serde import to_json
    from mi_companion.mi_editor.conversion.layers.from_hierarchy.solution import (
        convert_solution_layers_to_solution,
    )
    from mi_companion import MI_HIERARCHY_GROUP_NAME

    qgis_instance_handle = QgsProject.instance()

    layer_tree_root = QgsProject.instance().layerTreeRoot()

    mi_group = layer_tree_root.findGroup(MI_HIERARCHY_GROUP_NAME)

    if not mi_group:  # did not find the group
        logger.error("No Mi Hierarchy Group found")
        return

    if not isinstance(path, Path):
        path = Path(path)

    with InjectedProgressBar(parent=iface.mainWindow().statusBar()) as progress_bar:
        solutions = convert_solution_layers_to_solution(
            qgis_instance_handle,
            progress_bar=progress_bar,
            mi_group=mi_group,
            upload_venues=False,
        )
        for sol in solutions:
            with open(
                (path / f"{id(sol)}").with_suffix(SERIALISED_SOLUTION_EXTENSION), "w"
            ) as f:
                f.write(to_json(sol))
