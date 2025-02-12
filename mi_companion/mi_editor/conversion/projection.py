import typing
from typing import Optional

import pyproj
import shapely
from jord.shapely_utilities import clean_shape
from pandas import DataFrame

from mi_companion.configuration.options import read_bool_setting
from mi_companion.constants import (
    GDS_EPSG_NUMBER,
    MI_EPSG_NUMBER,
)

__all__ = [
    "prepare_geom_for_mi_db",
    "prepare_geom_for_qgis",
    "reproject_geometry_df",
    "should_reproject",
    "solve_target_crs_authid",
    "should_reproject_to_project",
    "get_target_crs_srsid",
    "get_target_crs_auth_id",
]

# GOOD RESOURCE FOR THIS IMPLEMENTATION: https://qgis.org/pyqgis/3.34/core/QgsCoordinateReferenceSystem.html
# ANOTHER: https://docs.qgis.org/3.34/en/docs/pyqgis_developer_cookbook/crs.html

# TODO: HONESTLY THIS FILE IS MESS; SHOULD BE REWORKED!

MI_CRS_AUTHID = f"EPSG:{MI_EPSG_NUMBER}"
MI_CRS = pyproj.CRS(MI_EPSG_NUMBER)


def get_back_projection() -> typing.Callable:
    destination_crs = pyproj.CRS(get_target_crs_auth_id())

    return pyproj.Transformer.from_crs(
        destination_crs, MI_CRS, always_xy=True
    ).transform


def get_forward_projection() -> typing.Callable:
    destination_crs = pyproj.CRS(get_target_crs_auth_id())

    return pyproj.Transformer.from_crs(
        MI_CRS, destination_crs, always_xy=True
    ).transform


def should_reproject() -> bool:
    target_crs = get_target_crs_auth_id()
    if read_bool_setting("REPROJECT_SHAPES"):
        if target_crs != MI_CRS_AUTHID:
            return True

    return False


def should_reproject_to_project() -> bool:
    return read_bool_setting("REPROJECT_TO_PROJECT_CRS")


def prepare_geom_for_mi_db(
    geom_shapely: shapely.geometry.base.BaseGeometry,
    clean: bool = True,
    back_projection: Optional[typing.Callable] = None,
) -> shapely.geometry.base.BaseGeometry:
    if back_projection is None:
        back_projection = get_back_projection()

    if should_reproject() and back_projection is not None:
        geom_shapely = shapely.ops.transform(back_projection, geom_shapely)

    if clean:
        return clean_shape(geom_shapely)

    return geom_shapely


def prepare_geom_for_qgis(
    geom_shapely: shapely.geometry.base.BaseGeometry,
    clean: bool = True,
    forward_projection: Optional[typing.Callable] = None,
) -> shapely.geometry.base.BaseGeometry:
    if forward_projection is None:
        forward_projection = get_forward_projection()

    if should_reproject() and forward_projection is not None:
        geom_shapely = shapely.ops.transform(forward_projection, geom_shapely)

    if clean:
        return clean_shape(geom_shapely)

    return geom_shapely


def reproject_geometry_df(df: DataFrame) -> DataFrame:
    df.set_crs(epsg=MI_EPSG_NUMBER, inplace=True, allow_override=True)

    if should_reproject():
        return df.to_crs(epsg=get_target_crs_srsid(), inplace=True)

    return df


def solve_target_crs_authid() -> str:
    # QgsProject.instance().setCrs(my_crs)
    # if iface.mapCanvas().mapRenderer().hasCrsTransformEnabled():
    #  my_crs = core.QgsCoordinateReferenceSystem(4326,core.QgsCoordinateReferenceSystem.EpsgCrsId)
    #  iface.mapCanvas().mapRenderer().setDestinationCrs(my_crs)
    # qgis.utils.iface.activeLayer().crs().toWkt()

    IGNORE_THIS = """
  prev_setting = iface.layerTreeCanvasBridge().autoSetupOnFirstLayer()
iface.layerTreeCanvasBridge().setAutoSetupOnFirstLayer(False)

# add layers, set crs, etc

def post_steps():
    iface.layerTreeCanvasBridge().setAutoSetupOnFirstLayer(prev_setting)

QTimer.singleShot(500, lambda: post_steps)

"""
    # noinspection PyUnresolvedReferences
    from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

    # iface.mapCanvas().mapSettings().destinationCrs().authid()
    # canvas.mapRenderer().destinationCrs().authid()

    target_crs_auth_id = get_target_crs_auth_id()

    if should_reproject():
        return target_crs_auth_id

    return MI_CRS_AUTHID


def get_target_crs_auth_id() -> str:
    # noinspection PyUnresolvedReferences
    from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

    if should_reproject_to_project:
        target_crs = QgsProject.instance().crs().authid()
    else:
        target_crs = f"EPSG:{GDS_EPSG_NUMBER}"

    return target_crs


def get_target_crs_srsid() -> int:
    # noinspection PyUnresolvedReferences
    from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

    if should_reproject_to_project:
        target_crs = QgsProject.instance().crs().srsid()
    else:
        target_crs = GDS_EPSG_NUMBER

    return target_crs
