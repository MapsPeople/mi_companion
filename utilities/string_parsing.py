import json
from typing import List, Tuple

import shapely.wkt

__all__ = ["extract_wkt_elements"]


def extract_wkt_elements(
    exception_str: str,
) -> List[Tuple[str, shapely.geometry.base.BaseGeometry]]:
    from jord.geopandas_utilities.serialisation.well_known_text import WktTypeEnum

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
            message_json = json.loads(stripped)
            exception_str = message_json["message"]

        elif exception_str[:2] == "'{":
            exception_str = exception_str.strip().strip("'")
            print(exception_str)
            message_json = json.loads(exception_str)
            exception_str = message_json["message"]

        split_str = ")'"

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

    return wkt_elements
