from typing import Any

import geopandas
from integration_system import Solution
from jord.qlive_utilities import add_shapely_layer, add_dataframe_layer
from qgis.core import (
    QgsVectorLayer,
    QgsFeature,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsProject,
    QgsLayerTreeGroup,
)


def layer_hierarchy_to_solution() -> Solution:
    layer_tree_root = QgsProject.instance().layerTreeRoot()

    cms_group = layer_tree_root.findGroup("CMS")

    if cms_group:
        for child in cms_group.children():
            if isinstance(child, QgsLayerTreeGroup):
                print("- group: " + child.name())
                if child.name() == "test":  # to check subgroups within test group
                    for sub_child in child.children():
                        if isinstance(sub_child, QgsLayerTreeGroup):
                            sub_child.name()

        return Solution(None, None, None)
