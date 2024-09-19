import pyproj
import shapely
from jord.shapely_utilities.base import clean_shape
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
]

SOURCE_CRS = pyproj.CRS(MI_EPSG_NUMBER)
DESTINATION_CRS = pyproj.CRS(GDS_EPSG_NUMBER)

FORWARD_PROJECTION = pyproj.Transformer.from_crs(
    SOURCE_CRS, DESTINATION_CRS, always_xy=True
).transform
BACK_PROJECTION = pyproj.Transformer.from_crs(
    DESTINATION_CRS, SOURCE_CRS, always_xy=True
).transform


def should_reproject() -> bool:
    return read_bool_setting("REPROJECT_SHAPES")


def prepare_geom_for_mi_db(
    geom_shapely: shapely.geometry.base.BaseGeometry,
    clean: bool = True,
    back_projection: callable = BACK_PROJECTION,
) -> shapely.geometry.base.BaseGeometry:
    if should_reproject() and back_projection is not None:
        geom_shapely = shapely.ops.transform(back_projection, geom_shapely)

    if clean:
        return clean_shape(geom_shapely)

    return geom_shapely


def prepare_geom_for_qgis(
    geom_shapely: shapely.geometry.base.BaseGeometry,
    clean: bool = True,
    forward_projection: callable = FORWARD_PROJECTION,
) -> shapely.geometry.base.BaseGeometry:
    if should_reproject() and forward_projection is not None:
        geom_shapely = shapely.ops.transform(forward_projection, geom_shapely)

    if clean:
        return clean_shape(geom_shapely)

    return geom_shapely


def reproject_geometry_df(df: DataFrame) -> DataFrame:
    if should_reproject():
        df.set_crs(epsg=MI_EPSG_NUMBER, inplace=True, allow_override=True)
        return df.to_crs(epsg=GDS_EPSG_NUMBER, inplace=True)

    return df
