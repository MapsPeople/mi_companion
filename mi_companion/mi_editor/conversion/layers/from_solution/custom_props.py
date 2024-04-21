import logging

from geopandas import GeoDataFrame

from mi_companion.configuration.constants import NULL_VALUE

logger = logging.getLogger(__name__)
__all__ = ["process_custom_props_df"]


def process_custom_props_df(rooms_df: GeoDataFrame) -> None:
    # TODO: !IH! IHIH
    # fix 'None', 'near landmark': 'None'}}
    # Unspecified:
    #     custom_properties:
    #       {'generic': {'alternative_name': None}}
    #     ->
    #     {'generic': {'alternative_name': 'None'}}

    for column_name, series in rooms_df.items():
        if "custom_properties" in column_name:
            if all(series.isna()) and False:
                rooms_df[column_name] = [None] * len(series)
            elif False:
                rooms_df[column_name] = rooms_df[column_name].fillna(NULL_VALUE)
    if False:
        rooms_df.fillna(NULL_VALUE, inplace=True)

    if False:
        for column_name, series in rooms_df.items():
            if "custom_properties" in column_name:
                rooms_df[column_name] = rooms_df[column_name].astype(str)
