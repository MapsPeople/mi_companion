import json
import logging
from typing import List, Tuple

import shapely
import shapely.wkt

__all__ = ["extract_wkt_elements"]

from mi_companion import NAN_VALUE, NULL_VALUE, STR_NA_VALUE, STR_NONE_VALUE

logger = logging.getLogger(__name__)


def is_json(my_json: str) -> bool:
    try:
        json_object = json.loads(my_json)
    except ValueError as e:
        return False
    return True


def extract_wkt_elements(
    exception_str: str,
) -> List[Tuple[str, shapely.geometry.base.BaseGeometry]]:
    from jord.geopandas_utilities import WktTypeEnum

    wkt_elements = []

    if exception_str:
        exception_str = exception_str.replace(
            "\\\\\\", "\\"
        )  # Replace triple escape with single
        exception_str = exception_str.replace("\\'", "'")

        l_strip = "HTTP response body: b'"
        if l_strip in exception_str:  # Try parse json
            stripped = str(exception_str).split(l_strip)[-1]
            stripped = stripped.strip().rstrip("'")
            if is_json(stripped):
                message_json = json.loads(stripped)
                exception_str = message_json["message"]

        elif exception_str[:2] == "'{":
            exception_str = exception_str.strip().strip("'")
            if is_json(exception_str):
                message_json = json.loads(exception_str)
                exception_str = message_json["message"]

        split_str = ")'"

        try:
            if exception_str:
                for geom_line in exception_str.split(split_str):
                    for wkt_qkey in {t.value.upper() for t in WktTypeEnum}:
                        if wkt_qkey in geom_line:
                            line = geom_line.split(f" {wkt_qkey} (")

                            if len(line) == 2:
                                context, element = line
                            elif len(line) == 1:
                                element = line[0]
                                context = None
                            else:
                                context, element, *wah = line

                            element = element.split(")'")[0]

                            wkt_elements.append(
                                (context, shapely.wkt.loads(f"{wkt_qkey} ({element})"))
                            )
        except Exception as e:
            logger.error("Error parsing")

    return wkt_elements


def is_str_value_null_like(v_str_):
    return (
        (v_str_ == NAN_VALUE.lower())
        or (v_str_ == NULL_VALUE.lower())
        or (v_str_ == STR_NA_VALUE.lower())
        or (v_str_ == STR_NONE_VALUE.lower())
        or len(v_str_.strip()) == 0
    )


if __name__ == "__main__":
    extract_wkt_elements()
