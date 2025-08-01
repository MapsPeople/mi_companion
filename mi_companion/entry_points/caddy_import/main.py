#!/usr/bin/python
import logging
from pathlib import Path
from typing import Optional

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtGui import QColor, QFont

# noinspection PyUnresolvedReferences
from qgis.core import (
    Qgis,
    QgsApplication,
    QgsFeature,
    QgsGeometry,
    QgsLayerTree,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsLayerTreeModel,
    QgsPalLayerSettings,
    QgsProject,
    QgsProject,
    QgsRasterLayer,
    QgsTextBufferSettings,
    QgsTextFormat,
    QgsVectorLayer,
    QgsVectorLayerSimpleLabeling,
)

from mi_companion import RESOURCE_BASE_PATH

logger = logging.getLogger(RESOURCE_BASE_PATH)

__all__ = ["run"]


def run(
    *,
    path: Path,
    text_column: Optional[str] = "text",
    layer_column: Optional[str] = "layer",
    crs_id: Optional[int] = 3857,
    font_size: Optional[int] = 6,
    oda_converter_path: Path = Path(
        r"C:\Program Files\ODA\ODAFileConverter 25.4.0\ODAFileConverter.exe"
    ),  # TODO: Use a bundled ODA converter?
) -> None:
    """
    Import an DXF file into the QGIS using the CADDY importer.

    :param oda_converter_path:
    :param path: Path to the directory containing the caddy files.
    :param text_column: Name of the column containing the text column.
    :param layer_column: Name of the column containing the layer column.
    :param crs_id: CRS ID to add the layer in.
    :param font_size: Font size of labels.
    :return:
    """
    from warg import system_open_path
    from jord.cad_utilities import convert_to_dxf
    from jord.qgis_utilities import categorise_layer

    from caddy.exporting import export_to

    """
alternative
by importing the DXF/DWG through the library libdxfrw into a geopackage (the method when you do Project >
Import/Export > Import Layers from DXF/DWG)
"""

    auto_add_layers: bool = True

    dwg_file_path = Path(path)

    if dwg_file_path.suffix == ".dwg":
        oda_converter_path_ = Path(oda_converter_path)

        if not oda_converter_path_.exists():
            logger.info("Oda converter was not found...")
            # TODO: Maybe run bundled installer?

        assert oda_converter_path_.exists(), f"{oda_converter_path} is not a valid path"
        new_dxf_path: Path = convert_to_dxf(dwg_file_path, oda_converter_path_)
    else:
        new_dxf_path = dwg_file_path

    out_path = new_dxf_path.with_suffix(".gpkg")

    export_to(new_dxf_path, out_path)

    logger.info(f"Emitted {new_dxf_path}")

    if True:
        if auto_add_layers:
            root = QgsProject.instance().layerTreeRoot()
            group_name = out_path.stem
            import_group = root.findGroup(group_name)
            if not import_group:
                import_group = root.insertGroup(0, group_name)

            out_path = str(out_path)
            layer = QgsVectorLayer(out_path, "DO_NOT_ADD_THIS!", "ogr")
            for sub_layer in layer.dataProvider().subLayers():
                _, name, _, geom_type, *_ = sub_layer.split("!!::!!")

                uri = ""
                uri += f"{out_path}|layername={name}|geometrytype={geom_type}"

                sub_v_layer = QgsVectorLayer(uri, name, "ogr")

                crs = sub_v_layer.crs()
                crs.createFromId(crs_id)
                sub_v_layer.setCrs(crs)
                if layer_column in sub_v_layer.fields().names():
                    categorise_layer(sub_v_layer, layer_column, outline_only=True)

                QgsProject.instance().addMapLayer(sub_v_layer, False)
                import_group.addLayer(sub_v_layer)

                if text_column:
                    layer_settings = QgsPalLayerSettings()
                    text_format = QgsTextFormat()

                    text_format.setFont(QFont("Arial", font_size))
                    text_format.setSize(font_size)

                    buffer_settings = QgsTextBufferSettings()
                    buffer_settings.setEnabled(True)
                    buffer_settings.setSize(1)
                    buffer_settings.setColor(QColor("white"))

                    text_format.setBuffer(buffer_settings)
                    layer_settings.setFormat(text_format)

                    layer_settings.fieldName = text_column
                    # layer_settings.placement = 2
                    layer_settings.placement = Qgis.LabelPlacement.OverPoint

                    layer_settings.enabled = True

                    layer_settings = QgsVectorLayerSimpleLabeling(layer_settings)
                    sub_v_layer.setLabelsEnabled(True)
                    sub_v_layer.setLabeling(layer_settings)
                    sub_v_layer.triggerRepaint()
        else:
            system_open_path(out_path)
