#!/usr/bin/python
import logging
from pathlib import Path

from warg import system_open_path

logger = logging.getLogger(__name__)


def run(
    *,
    path: str,
    auto_add_layers: bool = True,
    oda_converter_path: str = r"C:\Program Files\ODA\ODAFileConverter 25.4.0\ODAFileConverter.exe",
) -> None:
    """

    E.g. If duplicating a floor group to be picked as a Floor solution component make to include the describing tag (Floor)


    :param path:
    :param auto_add_layers:
    :param oda_converter_path:
    :return:
    """

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
    oda_converter_path_ = Path(oda_converter_path)
    assert oda_converter_path_.exists(), f"{oda_converter_path} is not a valid path"

    new_dxf_path: Path = convert_to_dxf(svg_file_path, oda_converter_path_)

    logger.info(f"Emitted {new_dxf_path}")

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
