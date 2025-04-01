#!/usr/bin/python
import logging

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup

# noinspection PyUnresolvedReferences
from qgis.utils import iface

logger = logging.getLogger(__name__)


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
