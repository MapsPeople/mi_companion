#!/usr/bin/python
import logging

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer

# noinspection PyUnresolvedReferences
from qgis.utils import iface
from typing import Optional

from mi_companion import RESOURCE_BASE_PATH

logger = logging.getLogger(RESOURCE_BASE_PATH)
__all__ = ["run"]


def run(
    *, new_name: str = "", randomize_fields: Optional[str] = "admin_id, external_id"
) -> None:
    """
    Duplicate selected group in layer tree view

    :param new_name:
    :param randomize_fields: What fields to randomize, separated by comma
    :return:
    """
    from jord.qgis_utilities.helpers import duplicate_groups, duplicate_tree_node

    # TODO: ADD INDIVIDUAL LAYER FUNCTIONALITY

    selected_nodes = iface.layerTreeView().selectedNodes()
    if len(selected_nodes) == 1:  # TODO: SHOULD WE ALLOW MORE?
        new_group = None
        for group in selected_nodes:
            if isinstance(group, QgsLayerTreeLayer):
                if new_name is ... or new_name == "" or new_name is None:
                    new_name = f"{group.name()} (Copy)"
                duplicate_tree_node(group.parent(), group, new_name=new_name)
            elif isinstance(group, QgsLayerTreeGroup):
                new_group, group_items = duplicate_groups(group, new_name=new_name)
            else:
                logging.error(
                    f"Selected Node is {group.name()} of type {type(group)}, not a QgsLayerTreeGroup"
                )
            if new_group:
                if randomize_fields:
                    for randomize_field in randomize_fields.split(","):
                        randomize_field = randomize_field.replace(" ", "")
                        from jord.qgis_utilities.helpers import randomize_sub_tree_field

                        randomize_sub_tree_field(new_group.children(), randomize_field)
    else:
        logging.error(f"There are {len(selected_nodes)}, please only select one")
