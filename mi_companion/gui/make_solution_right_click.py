import shapely
import uuid

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtCore, QtWidgets

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtWidgets import (
    QMessageBox,
)

# noinspection PyUnresolvedReferences
from qgis.core import (
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsMapLayerType,
    QgsProject,
)

# noinspection PyUnresolvedReferences
from qgis.gui import QgsMapLayerAction, QgsMapToolIdentify

# noinspection PyUnresolvedReferences
from qgis.utils import iface
from typing import Any

from jord.qgis_utilities import feature_to_shapely
from jord.qgis_utilities.helpers import reconnect_signal
from jord.shapely_utilities import clean_shape

# noinspection PyUnresolvedReferences
# from qgis.utils import iface

IDENTIFY_ACTIONS_AUGMENTED = SELECT_ACTIONS_AUGMENTED = False

__all__ = ["add_augmented_actions"]


def show_wkt_action_callable(layer: Any, feature: Any) -> None:
    """What our new action will do?"""
    QMessageBox.information(
        iface.mainWindow(),
        f"Feature's WKT ({layer.name()}:{feature.id()})",
        feature.geometry().asWkt(),
    )


def show_copy_action_callable(layer: Any, feature: Any) -> None:
    import pyperclip

    pyperclip.copy(feature.geometry().asWkt())


def show_make_solution_dialog_action_callable(layer: Any, feature: Any) -> None:
    """What our new action will do?"""

    QMessageBox.information(
        iface.mainWindow(),
        f"Feature's WKT ({layer.name()}:{feature.id()})",
        feature.geometry().asWkt(),
    )

    from sync_module.model import Solution
    from mi_companion.mi_editor import add_solution_layers

    name: str = "New Solution"
    customer_id: str = "4ba27f32c1034ca880431259"
    venue_name = "default"

    s = Solution(uuid.uuid4().hex.lower(), name, _customer_id=customer_id)

    venue_polygon = clean_shape(shapely.unary_union(feature_to_shapely(feature)))
    assert isinstance(
        venue_polygon, shapely.Polygon
    ), f"{venue_polygon=} must be shapely.Polygon"
    venue_key = s.add_venue(venue_name, venue_name, polygon=venue_polygon)
    building_key = s.add_building(
        venue_name, venue_name, polygon=venue_polygon, venue_key=venue_key
    )
    floor_key = s.add_floor(
        floor_index=0, building_key=building_key, name=venue_name, polygon=venue_polygon
    )
    s.add_room(venue_name, venue_name, polygon=venue_polygon, floor_key=floor_key)
    s.add_area(venue_name, venue_name, polygon=venue_polygon, floor_key=floor_key)
    s.add_point_of_interest(
        venue_name,
        venue_name,
        venue_polygon.representative_point(),
        floor_key=floor_key,
    )
    # s.add_graph()
    # s.add_door()
    # s.add_connection()

    root = QgsProject.instance().layerTreeRoot()

    add_solution_layers(
        qgis_instance_handle=None,
        solution=s,
        layer_tree_root=root,
    )


def add_augmented_actions(tool: Any, old_tool: Any) -> None:
    """Add the new action to the identify menu"""
    # global IDENTIFY_ACTIONS_AUGMENTED, SELECT_ACTIONS_AUGMENTED

    global IDENTIFY_ACTIONS_AUGMENTED

    if not IDENTIFY_ACTIONS_AUGMENTED and isinstance(tool, QgsMapToolIdentify):
        IDENTIFY_ACTIONS_AUGMENTED = True
        menu = tool.identifyMenu()

        show_wkt_action = QgsMapLayerAction(
            "Show feature's WKT",
            menu,
            QgsMapLayerType.VectorLayer,
            QgsMapLayerAction.SingleFeature,
        )
        reconnect_signal(show_wkt_action.triggeredForFeature, show_wkt_action_callable)
        menu.addCustomAction(show_wkt_action)

        copy_wkt_action = QgsMapLayerAction(
            "Copy WKT to clip-board",
            menu,
            QgsMapLayerType.VectorLayer,
            QgsMapLayerAction.SingleFeature,
        )
        reconnect_signal(copy_wkt_action.triggeredForFeature, show_copy_action_callable)
        menu.addCustomAction(copy_wkt_action)

        show_make_solution_dialog_action = QgsMapLayerAction(
            "Make solution for feature",
            menu,
            QgsMapLayerType.VectorLayer,
            QgsMapLayerAction.SingleFeature,
        )
        reconnect_signal(
            show_make_solution_dialog_action.triggeredForFeature,
            show_make_solution_dialog_action_callable,
        )
        menu.addCustomAction(show_make_solution_dialog_action)

    if False:
        if not SELECT_ACTIONS_AUGMENTED and isinstance(tool, QgsMapToolIdentify):
            IDENTIFY_ACTIONS_AUGMENTED = True
            menu = tool.identifyMenu()

            show_wkt_action = QgsMapLayerAction(
                "Show feature's WKT",
                menu,
                QgsMapLayerType.VectorLayer,
                QgsMapLayerAction.SingleFeature,
            )
            reconnect_signal(
                show_wkt_action.triggeredForFeature, show_wkt_action_callable
            )
            menu.addCustomAction(show_wkt_action)

            copy_wkt_action = QgsMapLayerAction(
                "Copy WKT to clip-board",
                menu,
                QgsMapLayerType.VectorLayer,
                QgsMapLayerAction.SingleFeature,
            )
            reconnect_signal(
                copy_wkt_action.triggeredForFeature, show_copy_action_callable
            )
            menu.addCustomAction(copy_wkt_action)

            show_make_solution_dialog_action = QgsMapLayerAction(
                "Make solution for feature",
                menu,
                QgsMapLayerType.VectorLayer,
                QgsMapLayerAction.SingleFeature,
            )
            reconnect_signal(
                show_make_solution_dialog_action.triggeredForFeature,
                show_make_solution_dialog_action_callable,
            )
            menu.addCustomAction(show_make_solution_dialog_action)
