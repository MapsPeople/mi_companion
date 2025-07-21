#!/usr/bin/python
import logging
import os
from pathlib import Path

# noinspection PyUnresolvedReferences
from qgis.core import (
    QgsApplication,
    QgsFeature,
    QgsGeometry,
    QgsLayerTree,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsLayerTreeModel,
    QgsProject,
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
)

from mi_companion import RESOURCE_BASE_PATH

logger = logging.getLogger(RESOURCE_BASE_PATH)

__all__ = ["run"]


def run(
    *,
    dwg_path: Path,
    # auto_add_layers: bool = True,
    oda_converter_path: Path = Path(
        r"C:\Program Files\ODA\ODAFileConverter 25.4.0\ODAFileConverter.exe"
    ),
) -> None:
    """

    E.g. If duplicating a floor group to be picked as a Floor solution component make to include the
    describing tag (Floor)


    :param dwg_path:
    :param auto_add_layers:
    :param oda_converter_path:
    :return:
    """
    from warg import system_open_path

    from jord.cad_utilities import convert_to_dxf

    """
alternative
by importing the DXF/DWG through the library libdxfrw into a geopackage (the method when you do Project >
Import/Export > Import Layers from DXF/DWG)
"""

    if isinstance(dwg_path, str):
        dwg_path = Path(dwg_path)

    if isinstance(oda_converter_path, str):
        oda_converter_path = Path(oda_converter_path)

    assert oda_converter_path.exists(), f"{oda_converter_path} is not a valid path"

    new_dxf_path: Path = convert_to_dxf(dwg_path, oda_converter_path)

    logger.info(f"Emitted {new_dxf_path}")

    auto_add_layers: bool = True
    if auto_add_layers:
        dfx_file = str(new_dxf_path)
        vector_layer = QgsVectorLayer(dfx_file, "layer_test", "ogr")
        sub_layers = vector_layer.dataProvider().subLayers()

        for s in sub_layers:
            geom_type = s.split("!!::!!")[3]

            uri = f"{dfx_file}|layername=entities|geometrytype={geom_type}"

            dfx_file_name = os.path.splitext(os.path.basename(dfx_file))[0]
            layer_name = f"{dfx_file_name} - {geom_type}"
            sub_vector_layer = QgsVectorLayer(uri, layer_name, "ogr")

            QgsProject.instance().addMapLayer(sub_vector_layer)

        # dxf_vl = QgsVectorLayer(new_dxf_path.stem + dxf_info, str(new_dxf_path), "ogr")
        # if dxf_vl.isValid() == True:
        #    QgsProject.instance().addMapLayer(dxf_vl)
    else:
        system_open_path(new_dxf_path.parent)
