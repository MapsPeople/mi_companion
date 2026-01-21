#!/usr/bin/python
import logging

from mi_companion import RESOURCE_BASE_PATH

_logger = logging.getLogger(RESOURCE_BASE_PATH)
__all__ = ["run"]
FUNCTION_DESCRIPTION = """Recompute field_name for all features in group
"""

__doc__ = FUNCTION_DESCRIPTION


def run(*, field_name: str = "admin_id") -> None:
    f"""{FUNCTION_DESCRIPTION}


    :param field_name:
    """
    # noinspection PyUnresolvedReferences
    from qgis.utils import iface
    from jord.qgis_utilities.helpers import randomize_sub_tree_field

    selected_nodes = iface.layerTreeView().selectedNodes()

    if len(selected_nodes) > 0:
        for n in iter(selected_nodes):
            randomize_sub_tree_field(n, field_name)
    else:
        _logger.error(f"Number of selected nodes was {len(selected_nodes)}")
        _logger.error(f"Please select node in the layer tree")
