#!/usr/bin/python
import logging

logger = logging.getLogger(__name__)

# noinspection PyUnresolvedReferences
from qgis.core import (
    QgsProject,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    Qgis,
)

from typing import Dict, Optional


def get_available_mi_layers() -> Dict[str, str]:
    """Returns a dictionary of available MI layers and their URLs"""
    return {
        "Standard MI Layer": "https://example.com/mi/standard",
        "Custom MI Layer": "https://example.com/mi/custom",
        "Template MI Layer": "https://example.com/mi/template",
    }


def download_mi_layer(url: str) -> Optional[dict]:
    """Downloads and returns MI layer data from URL"""
    import requests

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to download MI layer: {e}")
        return None


def create_mi_layer(layer_data: dict, layer_name: str) -> bool:
    """Creates a new MI layer from downloaded data"""
    from jord.qgis_utilities.fields import make_field_unique
    from jord.qlive_utilities import add_shapely_layer
    from jord.qgis_utilities.styling import set_3d_view_settings

    try:
        layer = add_shapely_layer(
            name=layer_name,
            geoms=[layer_data["geometry"]],
            columns=[layer_data["properties"]],
            crs=layer_data.get("crs", "EPSG:4326"),
            visible=True,
        )

        if layer:
            make_field_unique(layer)
            set_3d_view_settings(layer)
            return True

    except Exception as e:
        logger.error(f"Failed to create MI layer: {e}")

    return False


def run() -> None:
    """Add an MI layer to the project from available options"""
    from qgis.PyQt.QtWidgets import QInputDialog
    from qgis.utils import iface

    # Get available layers
    layers = get_available_mi_layers()

    # Show selection dialog
    layer_name, ok = QInputDialog.getItem(
        iface.mainWindow(),
        "Select MI Layer",
        "Available layers:",
        list(layers.keys()),
        editable=False,
    )

    if ok and layer_name:
        url = layers[layer_name]
        layer_data = download_mi_layer(url)

        if layer_data:
            if create_mi_layer(layer_data, layer_name):
                iface.messageBar().pushMessage(
                    "Success", f"Added MI layer: {layer_name}", level=Qgis.Success
                )
            else:
                iface.messageBar().pushMessage(
                    "Error",
                    f"Failed to create layer: {layer_name}",
                    level=Qgis.Critical,
                )
