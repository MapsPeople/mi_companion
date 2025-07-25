import logging
import typing
from typing import Optional

import numpy
import pyproj
import shapely
import shapely.geometry
from geopandas import GeoDataFrame

from jord.shapely_utilities import clean_shape
from mi_companion.configuration import read_bool_setting
from mi_companion.qgis_utilities.exceptions import InvalidReprojection
from sync_module.mi_sync_constants import (
    EDITING_CRS_AUTHID,
    EDITING_EPSG_NUMBER,
    MI_CRS_AUTHID,
    MI_EPSG_NUMBER,
)
from sync_module.shared.projection import MI_CRS

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


logger = logging.getLogger(__name__)


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


def back_project_qgis(
    geom: shapely.geometry.base.BaseGeometry,
) -> shapely.geometry.base.BaseGeometry:
    back = get_back_projection_qgis()
    if back is not None:
        return shapely.ops.transform(back, geom)

    return geom


def forward_project_qgis(
    geom: shapely.geometry.base.BaseGeometry,
) -> shapely.geometry.base.BaseGeometry:
    forward = get_forward_projection_qgis()

    if forward is not None:

        return shapely.ops.transform(forward, geom)

    return geom


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


def any_infinite_coords(geom_shapely: shapely.geometry.base.BaseGeometry) -> bool:
    """

    # Check for infinity in coordinates

    :param geom_shapely:
    :return:
    """
    coords = numpy.array(shapely.get_coordinates(geom_shapely))
    if any(not numpy.isfinite(coord) for coord in coords.flatten()):

        logger.warning("Reprojection resulted in infinite coordinates")
        return True

    return False


def is_valid_lon_lat(geom_shapely: shapely.geometry.base.BaseGeometry) -> bool:
    """Check if all coordinates are within valid longitude/latitude ranges.

    :param geom_shapely: Shapely geometry to check
    :return: True if all coordinates are within valid ranges
    """
    coords = list(shapely.get_coordinates(geom_shapely))
    for coord in coords:
        lon, lat = coord[0], coord[1]
        # Check longitude (-180 to 180) and latitude (-90 to 90) ranges
        if not (-180 <= lon <= 180) or not (-90 <= lat <= 90):
            logger.warning(f"Invalid coordinates found: lon={lon}, lat={lat}")
            return False

    return True


def is_valid_lon_lat_fast(
    geom_shapely: shapely.geometry.base.BaseGeometry,
) -> bool:  # Faster?
    """Check if all coordinates are within valid longitude/latitude ranges.

    This function checks if coordinates are within the valid range:
    longitude: -180 to 180
    latitude: -90 to 90

    :param geom_shapely: Shapely geometry to check
    :return: True if all coordinates are within valid ranges
    """
    coords = shapely.get_coordinates(geom_shapely)

    # Use numpy for faster validation
    if coords.size == 0:
        return True

    # Get min and max values for quick check
    min_x, min_y = numpy.min(coords, axis=0)
    max_x, max_y = numpy.max(coords, axis=0)

    # Quick check - if all bounds are within range, all coords are valid
    if -180 <= min_x <= max_x <= 180 and -90 <= min_y <= max_y <= 90:
        return True

    # Detailed check if the quick check fails
    valid_x = numpy.logical_and(coords[:, 0] >= -180, coords[:, 0] <= 180)
    valid_y = numpy.logical_and(coords[:, 1] >= -90, coords[:, 1] <= 90)

    if not numpy.all(valid_x):
        invalid_x = coords[~valid_x, 0]
        logger.warning(f"Invalid longitude values found: {invalid_x}")
        return False

    if not numpy.all(valid_y):
        invalid_y = coords[~valid_y, 1]
        logger.warning(f"Invalid latitude values found: {invalid_y}")
        return False

    return True


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

    if any_infinite_coords(geom_shapely):
        raise InvalidReprojection(
            f"Reproject of {geom_shapely} resulted in some coordinates becoming infinity, please check you coordinate systems"
        )

    # Check if reprojected coordinates are within valid ranges
    if not is_valid_lon_lat_fast(geom_shapely):
        raise InvalidReprojection(
            f"Reprojection of {geom_shapely} resulted in coordinates outside valid longitude/latitude range"
        )

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

    if any_infinite_coords(geom_shapely):
        raise InvalidReprojection(
            f"Reproject of {geom_shapely} resulted in some coordinates becoming infinity, please check you coordinate systems"
        )

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
