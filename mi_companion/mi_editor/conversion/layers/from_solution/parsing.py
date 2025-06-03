import dataclasses
import logging
from typing import Any

from geopandas import GeoDataFrame
from pandas.io.json._normalize import _simple_json_normalize

from integration_system.model.typings import Translations

logger = logging.getLogger(__name__)
__all__ = ["process_nested_fields_df", "translations_to_flattened_dict"]


def process_nested_fields_df(df: GeoDataFrame) -> None:

    for column_name, series in df.items():
        if "translations" in column_name:  # Drop custom properties
            if all(series.isna()):
                df.drop(columns=column_name, inplace=True)

            elif True:
                df[column_name] = series.astype(str)

    for column_name, series in df.items():
        if "display_rule" in column_name:  # Drop custom properties
            if all(series.isna()):
                df.drop(columns=column_name, inplace=True)

            elif True:
                df[column_name] = series.astype(str)

    for column_name, series in df.items():
        if "media" in column_name:  # Drop custom properties
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


def translations_to_flattened_dict(translations: Translations) -> dict[str, Any]:
    if translations is None:
        return {}

    return _simple_json_normalize(
        {
            f"translations.{language}": dataclasses.asdict(lb)
            for language, lb in translations.items()
        }
    )
