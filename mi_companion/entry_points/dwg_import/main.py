#!/usr/bin/python


from pathlib import Path


def run(*, path: str) -> None:
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

    from jord.qlive_utilities import add_dataframe_layer

    svg_file_path = Path(path)
    new_dxf_path: Path = convert_to_dxf(svg_file_path)

    # dxf_info = ""  # "|layername=entities|geometrytype=LineString"

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
