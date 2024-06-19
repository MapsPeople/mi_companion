#!/usr/bin/python
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def run(*, new_name: str = "", randomize_field: Optional[str] = "external_id") -> None:
    from jord.qgis_utilities.helpers import duplicate_groups

    # noinspection PyUnresolvedReferences
    from qgis.utils import iface

    # noinspection PyUnresolvedReferences
    from qgis.core import QgsLayerTreeGroup

    selected_nodes = iface.layerTreeView().selectedNodes()
    if len(selected_nodes) == 1:
        group = next(iter(selected_nodes))
        new_group = None
        if isinstance(group, QgsLayerTreeGroup):
            new_group, group_items = duplicate_groups(group, new_name=new_name)
        else:
            logging.error(
                f"Selected Node is {group.name()} of type {type(group)}, not a QgsLayerTreeGroup"
            )
        if new_group:
            if randomize_field:
                from jord.qgis_utilities.helpers import randomize_sub_tree_field

                randomize_sub_tree_field(new_group.children(), randomize_field)
    else:
        logging.error(f"There are {len(selected_nodes)}, please only select one")
