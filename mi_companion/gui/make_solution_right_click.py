from typing import Any

# noinspection PyUnresolvedReferences
from qgis.utils import iface

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject, QgsMapLayerType

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets, QtCore

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtWidgets import (
    QMessageBox,
)

# noinspection PyUnresolvedReferences
from qgis.gui import QgsMapLayerAction, QgsMapToolIdentify


from jord.qgis_utilities.helpers import reconnect_signal


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


def add_augmented_actions(tool: Any, old_tool: Any) -> None:
    """Add the new action to the identify menu"""
    global IDENTIFY_ACTIONS_AUGMENTED, SELECT_ACTIONS_AUGMENTED
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
