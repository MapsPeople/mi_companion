from typing import Any

# noinspection PyUnresolvedReferences
from qgis.core import QgsEditorWidgetSetup

from integration_system.model import Solution

__all__ = ["make_value_map_widget"]


def make_value_map_widget(solution: Solution) -> Any:
    return QgsEditorWidgetSetup(
        "ValueMap",
        {
            "map": {
                solution.location_types.get(k).name: solution.location_types.get(k).name
                for k in sorted(solution.location_types.keys)
            }
        },
    )
