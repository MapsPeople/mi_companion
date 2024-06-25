import pyproj

__all__ = [
    "prepare_geom_for_mi_db",
    "prepare_geom_for_qgis",
    "MI_EPSG_NUMBER",
    "GDS_EPSG_NUMBER",
    "reproject_geometry_df",
    "should_reproject",
    "INSERT_INDEX",
]

import shapely

from jord.shapely_utilities.base import clean_shape

from mi_companion.configuration.options import read_bool_setting

MI_EPSG_NUMBER = 4326
GDS_EPSG_NUMBER = 3857


def should_reproject() -> bool:
    return read_bool_setting("REPROJECT_SHAPES")


SOURCE_CRS = pyproj.CRS(MI_EPSG_NUMBER)
DESTINATION_CRS = pyproj.CRS(GDS_EPSG_NUMBER)
FORWARD_PROJECTION = pyproj.Transformer.from_crs(
    SOURCE_CRS, DESTINATION_CRS, always_xy=True
).transform
BACK_PROJECTION = pyproj.Transformer.from_crs(
    DESTINATION_CRS, SOURCE_CRS, always_xy=True
).transform


def prepare_geom_for_mi_db(
    geom_shapely: shapely.geometry.base.BaseGeometry,
) -> shapely.geometry.base.BaseGeometry:
    if should_reproject():
        geom_shapely = shapely.ops.transform(BACK_PROJECTION, geom_shapely)

    return clean_shape(geom_shapely)


def prepare_geom_for_qgis(
    geom_shapely: shapely.geometry.base.BaseGeometry,
) -> shapely.geometry.base.BaseGeometry:
    if should_reproject():
        geom_shapely = shapely.ops.transform(FORWARD_PROJECTION, geom_shapely)

    return clean_shape(geom_shapely)


def reproject_geometry_df(df):
    if should_reproject():
        df.set_crs(epsg=MI_EPSG_NUMBER, inplace=True, allow_override=True)
        return df.to_crs(epsg=GDS_EPSG_NUMBER, inplace=True)
    return df


INSERT_INDEX = 0  # if zero first, if one after hierarchy data
