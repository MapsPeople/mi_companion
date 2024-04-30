import logging

from geopandas import GeoDataFrame

from mi_companion.configuration.constants import NULL_VALUE

logger = logging.getLogger(__name__)
__all__ = ["process_custom_props_df"]


def process_custom_props_df(df: GeoDataFrame) -> None:
    # TODO: !IH! IHIH
    # fix 'None', 'near landmark': 'None'}}
    # Unspecified:
    #     custom_properties:
    #       {'generic': {'alternative_name': None}}
    #     ->
    #     {'generic': {'alternative_name': 'None'}}

    for column_name, series in df.items():
        if "custom_properties" in column_name:  # Drop custom properties
            if all(series.isna()):
                if False:
                    df[column_name] = [None] * len(series)
                else:  # Drop custom properties
                    df.drop(columns=column_name, inplace=True)
            elif False:
                df[column_name] = df[column_name].fillna(NULL_VALUE)

    for column_name, series in df.items():
        if len(series) > 0:
            if series.isna().iloc[0]:
                if not all(series.isna()):
                    # assert not any(series.isna())  # UNIFI TYPES!
                    example = series.notna().infer_objects().dtypes
                    df[column_name] = series.astype(example)

    converted_df = df.convert_dtypes()

    for column_name, series in converted_df.items():  # COPY OVER SERIES!
        df[column_name] = series

    if False:
        for column_name, series in df.items():
            if "custom_properties" in column_name:
                if series.apply(type).nunique() > 1:
                    logger.error(series.dtypes)

    if False:
        df.applymap(type).nunique().eq(1).sum()

    if False:
        df.fillna(NULL_VALUE, inplace=True)

    if False:
        for column_name, series in df.items():
            if "custom_properties" in column_name:
                df[column_name] = df[column_name].astype(str)

    if False:
        for column_name, series in df.items():
            assert not all(series.isna()), f"{column_name}:\n{series}"
