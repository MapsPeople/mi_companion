import copy
import dataclasses
import json
import logging
from typing import Collection, Mapping

from geopandas import GeoDataFrame
from pandas import DataFrame, json_normalize

from integration_system.model import CollectionMixin
from mi_companion import NULL_VALUE, REAL_NONE_JSON_VALUE

logger = logging.getLogger(__name__)
__all__ = ["process_custom_props_df", "to_df"]


def process_custom_props_df(df: GeoDataFrame) -> None:
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


def to_df_2(coll_mix: CollectionMixin) -> DataFrame:
    # noinspection PyTypeChecker
    cs = []
    for c in coll_mix:
        if c and hasattr(c, "custom_properties"):
            cps = getattr(c, "custom_properties")
            if cps is not None:
                if isinstance(cps, Mapping) and len(cps):
                    for language, translations in copy.deepcopy(cps).items():
                        for cp, cpv in translations.items():
                            if cpv is None:
                                cps[language][cp] = REAL_NONE_JSON_VALUE

                    setattr(c, "custom_properties", cps)

                else:
                    setattr(c, "custom_properties", None)

        cs.append(dataclasses.asdict(c))

    return json_normalize(cs)


def to_df(coll_mix: CollectionMixin) -> DataFrame:
    # noinspection PyTypeChecker
    cs = []
    for c in coll_mix:
        if hasattr(c, "custom_properties"):
            cps = getattr(c, "custom_properties")
            if cps is not None:
                for language, translations in copy.deepcopy(cps).items():
                    for cp, cpv in translations.items():
                        if cpv is None:
                            cps[language][cp] = REAL_NONE_JSON_VALUE

                setattr(c, "custom_properties", cps)

        c_d = dataclasses.asdict(c)

        if "categories" in c_d:
            list_of_category_dicts = c_d.pop("categories")

            keys = []
            if list_of_category_dicts:
                for cat in list_of_category_dicts:
                    if False:
                        a = json.loads(cat["name"])
                        if isinstance(a, str):
                            keys.append(a)
                        elif isinstance(a, Collection):
                            keys.extend(a)
                        else:
                            raise NotImplementedError(f"{type(a)} is not supported")
                    else:
                        keys.append(cat["name"])

            c_d["category_keys"] = keys

        cs.append(c_d)

    return json_normalize(cs)
