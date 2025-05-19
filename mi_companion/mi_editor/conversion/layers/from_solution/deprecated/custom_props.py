import logging

from geopandas import GeoDataFrame

from mi_companion import NULL_VALUE

logger = logging.getLogger(__name__)
__all__ = ["process_custom_props_df32423"]


def process_custom_props_df32423(df: GeoDataFrame) -> None:
    """
    UPDATE: Venue(s):
      Updating
        Venue: Amsterdam - Schiphol Airport (AMS):
            custom_properties:
              {'en': {'lastauditedtimestamp': 'None'}}
            ->
            {'en': {'lastauditedtimestamp': None}}

    UPDATE: Area(s):
      Updating
        Area: Restroom, Floor: 1, Building: Building 0, Venue: Amsterdam - Schiphol Airport (AMS):
            custom_properties:
              {}
            ->
            {'generic': {'transform': 'True', 'servicetype': 'True', 'markupjson': 'True'}}
        Area: Transfer Desk, Floor: 1, Building: Building 0, Venue: Amsterdam - Schiphol Airport (AMS):
            custom_properties:
              {'generic': {'transform': 'None', 'servicetype': 'Transfer Desk', 'markupjson': 'None'}}
            ->
            {'generic': {'transform': 'True', 'servicetype': 'True', 'markupjson': 'True'}}
        Area: Restroom, Floor: 1, Building: Building 0, Venue: Amsterdam - Schiphol Airport (AMS):
            custom_properties:
              {}
            ->
            {'generic': {'transform': 'True', 'servicetype': 'True', 'markupjson': 'True'}}

            :param df:
            :return:
    """

    IGNORE_THIS = """
            apply works on a row / column basis of a DataFrame
    applymap works element-wise on a DataFrame
    map works element-wise on a Series
            """

    if False:
        for column_name, series in df.items():
            if "custom_properties" in column_name:
                if series.apply(type).nunique() > 1:
                    logger.error(series.dtypes)

    for column_name, series in df.items():
        if "custom_properties" in column_name:  # Drop custom properties
            if all(series.isna()):
                if False:
                    df[column_name] = [None] * len(series)
                else:  # Drop custom properties
                    df.drop(columns=column_name, inplace=True)

            elif True:
                df[column_name] = series.astype(str)

            elif False:
                df[column_name] = df[column_name].fillna(NULL_VALUE)

    for column_name, series in df.items():
        if "display_rule" in column_name:  # Drop custom properties
            if all(series.isna()):
                if False:
                    df[column_name] = [None] * len(series)
                else:  # Drop custom properties
                    df.drop(columns=column_name, inplace=True)

            elif True:
                df[column_name] = series.astype(str)

            elif False:
                df[column_name] = df[column_name].fillna(NULL_VALUE)

    for column_name, series in df.items():
        if "media" in column_name:  # Drop custom properties
            if all(series.isna()):
                if False:
                    df[column_name] = [None] * len(series)
                else:  # Drop custom properties
                    df.drop(columns=column_name, inplace=True)

            elif True:
                df[column_name] = series.astype(str)

            elif False:
                df[column_name] = df[column_name].fillna(NULL_VALUE)

    if False:
        for column_name, series in df.items():
            if "details" in column_name:  # Drop custom properties
                if all(series.isna()):
                    if False:
                        df[column_name] = [None] * len(series)
                    else:  # Drop custom properties
                        df.drop(columns=column_name, inplace=True)

                elif True:
                    df[column_name] = series.astype(str)

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
                    logger.error(series.apply(lambda a: str(type(a))))

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
