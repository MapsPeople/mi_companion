#!/usr/bin/python


import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def run(*, path: str) -> None:
    from svaguely import parse_svg
    from warg import flatten_mapping

    # noinspection PyUnresolvedReferences
    # from qgis.utils import iface
    from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

    from jord.qlive_utilities import add_dataframe_layer
    import geopandas

    svg_file_path = Path(path)
    svg_elements, _ = parse_svg(svg_file_path, output_space=1)

    svg_elements = flatten_mapping(svg_elements)

    geoms = [g.geometry for g in svg_elements.values()]

    df = geopandas.GeoDataFrame(
        {"names": svg_elements.keys(), "geometry": geoms},
        crs="EPSG:3857",
        geometry="geometry",
    )

    add_dataframe_layer(
        qgis_instance_handle=QgsProject.instance(),
        dataframe=df,
        geometry_column="geometry",
        name=str(path),
        crs="EPSG:3857",
        # crs=f"EPSG:{GDS_EPSG_NUMBER if should_reproject() else MI_EPSG_NUMBER }",
    )
