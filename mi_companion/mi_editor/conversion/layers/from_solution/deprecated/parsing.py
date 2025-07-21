import copy
import dataclasses
from typing import Mapping

from geopandas import GeoDataFrame
from pandas import DataFrame, json_normalize

from integration_system.model.solution_item import CollectionMixin
from jord.qgis_utilities import REAL_NONE_JSON_VALUE


def process_nested_str_map_df(df: GeoDataFrame, *, nested_map_field_name: str) -> None:
    """
    UPDATE: Venue(s):
      Updating
        Venue: Amsterdam - Schiphol Airport (AMS):
            translations:
              {'en': {'lastauditedtimestamp': 'None'}}
            ->
            {'en': {'lastauditedtimestamp': None}}

    UPDATE: Area(s):
      Updating
        Area: Restroom, Floor: 1, Building: Building 0, Venue: Amsterdam - Schiphol Airport (AMS):
            translations:
              {}
            ->
            {'generic': {'transform': 'True', 'servicetype': 'True', 'markupjson': 'True'}}
        Area: Transfer Desk, Floor: 1, Building: Building 0, Venue: Amsterdam - Schiphol Airport (AMS):
            translations:
              {'generic': {'transform': 'None', 'servicetype': 'Transfer Desk', 'markupjson': 'None'}}
            ->
            {'generic': {'transform': 'True', 'servicetype': 'True', 'markupjson': 'True'}}
        Area: Restroom, Floor: 1, Building: Building 0, Venue: Amsterdam - Schiphol Airport (AMS):
            translations:
              {}
            ->
            {'generic': {'transform': 'True', 'servicetype': 'True', 'markupjson': 'True'}}

    :param nested_map_field_name:
    :param df:
    :return:
    """

    for column_name, series in df.items():
        if nested_map_field_name in column_name:  # Drop custom properties
            if all(series.isna()):
                df.drop(columns=column_name, inplace=True)

            elif True:
                df[column_name] = series.astype(str)

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


def to_df_2(coll_mix: CollectionMixin) -> DataFrame:
    # noinspection PyTypeChecker
    cs = []
    for c in coll_mix:
        if c and hasattr(c, "translations"):
            cps = getattr(c, "translations")
            if cps is not None:
                if isinstance(cps, Mapping) and len(cps):
                    for language, translations in copy.deepcopy(cps).items():
                        for cp, cpv in translations.items():
                            if cpv is None:
                                cps[language][cp] = REAL_NONE_JSON_VALUE

                    setattr(c, "translations", cps)

                else:
                    setattr(c, "translations", None)

        cs.append(dataclasses.asdict(c))

    return json_normalize(cs)
