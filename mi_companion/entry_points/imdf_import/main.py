#!/usr/bin/python


import logging
from pathlib import Path

from samples.loading import parse_imdf

logger = logging.getLogger(__name__)


def run(*, imdf_zip_file_path: Path) -> None:
    # noinspection PyUnresolvedReferences
    # from qgis.utils import iface
    from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

    from jord.qlive_utilities import add_dataframe_layer

    if isinstance(imdf_zip_file_path, str):
        imdf_zip_file_path = Path(imdf_zip_file_path)

    imdf_hierarchy = parse_imdf(imdf_zip_file_path)

    df = None

    add_dataframe_layer(
        qgis_instance_handle=QgsProject.instance(),
        dataframe=df,
        geometry_column="geometry",
        name=str(imdf_zip_file_path),
        crs="EPSG:3857",
        # crs=f"EPSG:{GDS_EPSG_NUMBER if should_reproject() else MI_EPSG_NUMBER }",
    )
