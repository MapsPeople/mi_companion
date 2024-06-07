#!/usr/bin/python
import logging
from pathlib import Path
from typing import Optional

from warg import system_open_path

logger = logging.getLogger(__name__)


def run(
    *,
    path: str,
    auto_add_layers: bool = True,
    oda_converter_path: str = r"C:\Program Files\ODA\ODAFileConverter 25.4.0\ODAFileConverter.exe",
) -> None:
    from jord.cad_utilities import convert_to_dxf
    import os

    # noinspection PyUnresolvedReferences
    # from qgis.utils import iface
    from qgis.core import (
        QgsLayerTreeGroup,
        QgsLayerTreeLayer,
        QgsProject,
        QgsApplication,
        QgsFeature,
        QgsGeometry,
        QgsLayerTree,
        QgsLayerTreeModel,
        QgsProject,
        QgsRasterLayer,
        QgsVectorLayer,
    )

    """
    alternative
    by importing the DXF/DWG through the library libdxfrw into a geopackage (the method when you do Project > Import/Export > Import Layers from DXF/DWG)
    """

    svg_file_path = Path(path)
    new_dxf_path: Path = convert_to_dxf(svg_file_path, oda_converter_path)

    logger.info(f"Emitted {new_dxf_path}")
    # dxf_info = ""  # "|layername=entities|geometrytype=LineString"

    if auto_add_layers:
        dfx_file = str(new_dxf_path)
        vlayer = QgsVectorLayer(dfx_file, "layer_test", "ogr")
        subLayers = vlayer.dataProvider().subLayers()

        # For each sublayer, diferent type of geometry, load a layer to map.
        for subLayer in subLayers:
            # Extract the geometry type
            geom_type = subLayer.split("!!::!!")[3]
            # Set the path
            uri = "{}|layername=entities|geometrytype={}".format(
                dfx_file,
                geom_type,
            )
            # Name for sub layer
            dfx_file_name = os.path.splitext(os.path.basename(dfx_file))[0]
            layer_name = f"{dfx_file_name} - {geom_type}"
            # Create layer
            sub_vlayer = QgsVectorLayer(uri, layer_name, "ogr")
            # Add layer to map
            QgsProject.instance().addMapLayer(sub_vlayer)

        # dxf_vl = QgsVectorLayer(new_dxf_path.stem + dxf_info, str(new_dxf_path), "ogr")
        # if dxf_vl.isValid() == True:
        #    QgsProject.instance().addMapLayer(dxf_vl)
    else:
        system_open_path(new_dxf_path.parent)
