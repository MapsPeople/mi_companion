from typing import Any, Mapping

# noinspection PyUnresolvedReferences
from qgis.core import QgsEditorWidgetSetup

__all__ = ["make_value_map_widget"]


def make_value_map_widget(mapp: Mapping[str, str]) -> Any:
    return QgsEditorWidgetSetup(
        "ValueMap",
        {"map": mapp},
    )
