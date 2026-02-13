#!/usr/bin/python
import logging
from qgis.core import QgsLayerTreeGroup
from qgis.utils import iface

from mi_companion import RESOURCE_BASE_PATH

_logger = logging.getLogger(RESOURCE_BASE_PATH)
__all__ = ["run"]
FUNCTION_DESCRIPTION = """...
"""
__doc__ = FUNCTION_DESCRIPTION


def run(*, appendix: str = " (Copy)") -> None:
    from jord.qgis_utilities.helpers import duplicate_groups

    selected_nodes = iface.layerTreeView().selectedNodes()
    if len(selected_nodes) == 1:
        group = next(iter(selected_nodes))
        if isinstance(group, QgsLayerTreeGroup):
            duplicate_groups(group, appendix=appendix)
        else:
            raise ValueError(
                f"Selected Node is {group.name()} of type {type(group)}, not a QgsLayerTreeGroup"
            )
    else:
        raise ValueError(f"There are {len(selected_nodes)}, please only select one")
