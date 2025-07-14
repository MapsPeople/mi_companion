import typing
from typing import Optional

import pyproj
import shapely
from geopandas import GeoDataFrame
from shapely.geometry.base import BaseGeometry

from integration_system.projection import MI_CRS
from jord.shapely_utilities import clean_shape
from mi_companion.configuration.options import read_bool_setting
from integration_system.mi_sync_constants import (
    EDITING_CRS_AUTHID,
    EDITING_EPSG_NUMBER,
    MI_CRS_AUTHID,
    MI_EPSG_NUMBER,
)

__all__ = [
    "prepare_geom_for_mi_db_qgis",
    "prepare_geom_for_editing_qgis",
    "reproject_geometry_df_qgis",
    "should_reproject_qgis",
    "should_reproject_to_project_qgis",
    "get_forward_projection_qgis",
    "get_back_projection_qgis",
    "get_target_crs_srsid",
    "solve_target_crs_authid",
    "get_target_crs_auth_id",
    "forward_project_qgis",
    "back_project_qgis",
]

# GOOD RESOURCE FOR THIS IMPLEMENTATION: https://qgis.org/pyqgis/3.34/core/QgsCoordinateReferenceSystem.html
# ANOTHER: https://docs.qgis.org/3.34/en/docs/pyqgis_developer_cookbook/crs.html

# TODO: HONESTLY THIS FILE IS MESS; SHOULD BE REWORKED!


def get_back_projection_qgis() -> typing.Callable:
    """

    :return:
    """
    destination_crs = pyproj.CRS(get_target_crs_auth_id())

    return pyproj.Transformer.from_crs(
        destination_crs, MI_CRS, always_xy=True
    ).transform


def get_forward_projection_qgis() -> typing.Callable:
    """

    :return:
    """
    destination_crs = pyproj.CRS(get_target_crs_auth_id())

    return pyproj.Transformer.from_crs(
        MI_CRS, destination_crs, always_xy=True
    ).transform


def back_project_qgis(geom: BaseGeometry) -> BaseGeometry:
    return shapely.ops.transform(get_back_projection_qgis(), geom)


def forward_project_qgis(geom: BaseGeometry) -> BaseGeometry:
    return shapely.ops.transform(get_forward_projection_qgis(), geom)


def should_reproject_qgis() -> bool:
    """

    :return:
    """
    target_crs = get_target_crs_auth_id()

    if read_bool_setting("REPROJECT_SHAPES"):
        if target_crs != MI_CRS_AUTHID:
            return True

    return False


def should_reproject_to_project_qgis() -> bool:
    """

    :return:
    """
    return read_bool_setting("REPROJECT_TO_PROJECT_CRS")


def prepare_geom_for_mi_db_qgis(
    geom_shapely: shapely.geometry.base.BaseGeometry,
    clean: bool = True,
    back_projection: Optional[typing.Callable] = None,
) -> shapely.geometry.base.BaseGeometry:
    """

    :param geom_shapely:
    :param clean:
    :param back_projection:
    :return:
    """
    if back_projection is None:
        back_projection = get_back_projection_qgis()

    if should_reproject_qgis() and back_projection is not None:
        geom_shapely = shapely.ops.transform(back_projection, geom_shapely)

    if clean:
        return clean_shape(geom_shapely)

    return geom_shapely


def prepare_geom_for_editing_qgis(
    geom_shapely: shapely.geometry.base.BaseGeometry,
    clean: bool = True,
    forward_projection: Optional[typing.Callable] = None,
) -> shapely.geometry.base.BaseGeometry:
    """

    :param geom_shapely:
    :param clean:
    :param forward_projection:
    :return:
    """
    if forward_projection is None:
        forward_projection = get_forward_projection_qgis()

    if should_reproject_qgis() and forward_projection is not None:
        geom_shapely = shapely.ops.transform(forward_projection, geom_shapely)

    if clean:
        return clean_shape(geom_shapely)

    return geom_shapely


def reproject_geometry_df_qgis(df: GeoDataFrame) -> GeoDataFrame:
    """

    :param df:
    :return:
    """
    df.set_crs(epsg=MI_EPSG_NUMBER, inplace=True, allow_override=True)

    if should_reproject_qgis():
        return df.to_crs(epsg=get_target_crs_srsid(), inplace=True)

    return df


def solve_target_crs_authid() -> str:
    """

    :return:
    """
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

    # iface.mapCanvas().mapSettings().destinationCrs().authid()
    # canvas.mapRenderer().destinationCrs().authid()

    target_crs_auth_id = get_target_crs_auth_id()

    if should_reproject_qgis():
        return target_crs_auth_id

    return MI_CRS_AUTHID


def get_target_crs_auth_id() -> str:
    """

    :return:
    """
    if should_reproject_to_project_qgis:
        # noinspection PyUnresolvedReferences
        from qgis.core import QgsProject

        target_crs = QgsProject.instance().crs().authid()
    else:
        target_crs = EDITING_CRS_AUTHID

    return target_crs


def get_target_crs_srsid() -> int:
    """

    :return:
    """
    if should_reproject_to_project_qgis:
        # noinspection PyUnresolvedReferences
        from qgis.core import QgsProject

        target_crs = QgsProject.instance().crs().srsid()
    else:
        target_crs = EDITING_EPSG_NUMBER

    return target_crs
