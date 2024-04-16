#!/usr/bin/python
import uuid


def run(*, field_name="external_id") -> None:
    # noinspection PyUnresolvedReferences
    from qgis.utils import iface
    from jord.qgis_utilities.helpers import randomize_sub_tree_field

    selected_nodes = iface.layerTreeView().selectedNodes()

    if len(selected_nodes):
        randomize_sub_tree_field(selected_nodes, field_name)
    else:
        raise ValueError(f"There are {len(selected_nodes)}, please only select one")
