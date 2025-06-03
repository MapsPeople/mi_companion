#!/usr/bin/python

import logging
from pathlib import Path

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

# noinspection PyUnresolvedReferences
from qgis.utils import iface
from warg import system_open_path

logger = logging.getLogger(__name__)
SERIALISED_SOLUTION_EXTENSION = ".json"


def run(*, path: Path, open_folder_on_completion: bool = False) -> None:
    from jord.qgis_utilities.helpers import InjectedProgressBar

    from integration_system.tools.serialisation import to_json
    from mi_companion.mi_editor.conversion.layers.from_hierarchy.solution import (
        convert_solution_layers_to_solution,
    )
    from mi_companion.layer_descriptors import DATABASE_GROUP_DESCRIPTOR

    qgis_instance_handle = QgsProject.instance()

    layer_tree_root = QgsProject.instance().layerTreeRoot()

    mi_group = layer_tree_root.findGroup(DATABASE_GROUP_DESCRIPTOR)

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
        if solutions is None:
            logger.warning("No solutions found")
            return

        for sol in solutions:
            with open(
                (path / f"{id(sol)}").with_suffix(SERIALISED_SOLUTION_EXTENSION), "w"
            ) as f:
                f.write(to_json(sol))

    if open_folder_on_completion:
        system_open_path(path)
