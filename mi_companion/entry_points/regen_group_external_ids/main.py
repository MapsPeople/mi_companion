#!/usr/bin/python
import logging

logger = logging.getLogger(__name__)


def run(*, field_name: str = "external_id") -> None:
    # noinspection PyUnresolvedReferences
    from qgis.utils import iface
    from jord.qgis_utilities.helpers import randomize_sub_tree_field

    selected_nodes = iface.layerTreeView().selectedNodes()

    if len(selected_nodes) > 0:
        for n in iter(selected_nodes):
            randomize_sub_tree_field(n, field_name)
    else:
        logger.error(f"Number of selected nodes was {len(selected_nodes)}")
        logger.error(f"Please select node in the layer tree")
