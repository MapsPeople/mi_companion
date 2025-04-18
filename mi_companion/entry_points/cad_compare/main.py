#!/usr/bin/python

import logging
from pathlib import Path

# noinspection PyUnresolvedReferences
from qgis.core import QgsProject

from mi_companion import RESOURCE_BASE_PATH

logger = logging.getLogger(RESOURCE_BASE_PATH)

__all__ = []


def run(*, original_dxf_path: Path, new_dxf_path: Path) -> None:
    """
    Compares a new DXF files against a reference DXF file.
    :param original_dxf_path: Path to the original DXF file.
    :param new_dxf_path: Path to the new DXF file.
    :return:
    """
    import geopandas

    from caddy.difference import get_entity_differences

    if isinstance(original_dxf_path, str):
        original_dxf_path = Path(original_dxf_path)

    if isinstance(new_dxf_path, str):
        new_dxf_path = Path(new_dxf_path)

    diff = get_entity_differences(original_dxf_path, new_dxf_path)

    if True:
        from jord.qlive_utilities import add_dataframe_layer

        diff_geoms = geopandas.GeoDataFrame(
            (
                {"handle": k, "geometry": v["diffbuffer"]}
                for k, v in diff.items()
                if "diffbuffer" in v and v["diffbuffer"] is not None
            ),
            crs="EPSG:3857",
            geometry="geometry",
        )
        if not diff_geoms.empty:
            add_dataframe_layer(
                qgis_instance_handle=QgsProject.instance(),
                dataframe=diff_geoms,
                geometry_column="geometry",
                name="diffbuffer",
                crs="EPSG:3857",
                # crs=f"EPSG:{GDS_EPSG_NUMBER if should_reproject() else MI_EPSG_NUMBER }",
            )

    if True:
        from jord.qlive_utilities import add_dataframe_layer

        added_geoms = geopandas.GeoDataFrame(
            (
                {"handle": k, "geometry": v["added geometry"]}
                for k, v in diff.items()
                if "added geometry" in v and v["added geometry"] is not None
            ),
            crs="EPSG:3857",
            geometry="geometry",
        )
        if not added_geoms.empty:
            add_dataframe_layer(
                qgis_instance_handle=QgsProject.instance(),
                dataframe=added_geoms,
                geometry_column="geometry",
                name="added",
                crs="EPSG:3857",
                # crs=f"EPSG:{GDS_EPSG_NUMBER if should_reproject() else MI_EPSG_NUMBER }",
            )

    if True:
        from jord.qlive_utilities import add_dataframe_layer

        remaining_geoms = geopandas.GeoDataFrame(
            (
                {"handle": k, "geometry": v["remaining geometry"]}
                for k, v in diff.items()
                if "remaining geometry" in v and v["remaining geometry"] is not None
            ),
            crs="EPSG:3857",
            geometry="geometry",
        )
        if not remaining_geoms.empty:
            add_dataframe_layer(
                qgis_instance_handle=QgsProject.instance(),
                dataframe=remaining_geoms,
                geometry_column="geometry",
                name="remaining",
                crs="EPSG:3857",
                # crs=f"EPSG:{GDS_EPSG_NUMBER if should_reproject() else MI_EPSG_NUMBER }",
            )

    if True:
        from jord.qlive_utilities import add_dataframe_layer

        removed_geoms = geopandas.GeoDataFrame(
            (
                {"handle": k, "geometry": v["removed geometry"]}
                for k, v in diff.items()
                if "removed geometry" in v and v["removed geometry"] is not None
            ),
            crs="EPSG:3857",
            geometry="geometry",
        )
        if not removed_geoms.empty:
            add_dataframe_layer(
                qgis_instance_handle=QgsProject.instance(),
                dataframe=removed_geoms,
                geometry_column="geometry",
                name="removed",
                crs="EPSG:3857",
                # crs=f"EPSG:{GDS_EPSG_NUMBER if should_reproject() else MI_EPSG_NUMBER }",
            )
