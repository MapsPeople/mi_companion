import json
import logging
from typing import Any, List, Tuple

import shapely
import shapely.wkt

__all__ = ["extract_wkt_elements", "is_str_value_null_like", "is_json", "parse_q_value"]

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


def is_str_value_null_like(v_str_) -> bool:
    return (
        (v_str_ == NAN_VALUE.lower())
        or (v_str_ == NULL_VALUE.lower())
        or (v_str_ == STR_NA_VALUE.lower())
        or (v_str_ == STR_NONE_VALUE.lower())
        or len(v_str_.strip()) == 0
    )


def parse_q_value(v: Any) -> Any:
    # noinspection PyUnresolvedReferences
    from qgis.PyQt.QtCore import QVariant

    if isinstance(v, QVariant):
        if v.isNull():
            v = None
        else:
            v = v.value()

    return v


if __name__ == "__main__":
    extract_wkt_elements(
        "GEOMETRYCOLLECTION (POLYGON ((-1.013080440097465 1.00008030103449, 0.9802702725182121 "
        "0.9802709685731866, 1.0001280127339383 -1.0131163892522457, 0.85 -0.9, -0.9 -0.9, "
        "-0.9 0.8500000000000003, -1.013080440097465 1.00008030103449)), POLYGON ((1.019731748768209 "
        "0.9805437100213221, 2.9802675555205336 0.9805437100213221, 3.000128012733939 -1.013116389252246, "
        "2.85 -0.9, 1.15 -0.9, 0.9999196989655098 -1.013080440097465, 1.019731748768209 0.9805437100213221)), "
        "POLYGON ((3.0197290314268135 0.980270272518212, 5.0131163892522475 1.000128012733938, "
        "4.9 0.8500000000000002, 4.9 -0.9, 3.15 -0.9, 2.9999196989655097 -1.0130804400974647, 3.0197290314268135 "
        "0.980270272518212)), POLYGON ((-1.0130804400974653 3.0000803010344903, 0.9805437100213221 "
        "2.9802682512317915, 0.9805437100213221 1.019732444479466, -1.0131163892522457 0.9998719872660614, "
        "-0.9 1.15, -0.9 2.85, -1.0130804400974653 3.0000803010344903)), POLYGON ((1.019456289978678 "
        "2.980543710021322, 2.980543710021322 2.980543710021322, 2.980543710021322 1.019456289978678, "
        "1.019456289978678 1.019456289978678, 1.019456289978678 2.980543710021322)), POLYGON ((3.019456289978678 "
        "2.9802675555205336, 5.013116389252247 3.0001280127339385, 4.9 2.850000000000001, "
        "4.9 1.1500000000000001, 5.013080440097467 0.9999196989655101, 3.019456289978678 1.019731748768209, "
        "3.019456289978678 2.9802675555205336)), POLYGON ((-1.013116389252246 2.999871987266061, -0.9 3.15, "
        "-0.9 4.9, 0.85 4.9, 1.0000803010344899 5.013080440097467, 0.9802709685731866 3.019729727481788, "
        "-1.013116389252246 2.999871987266061)), POLYGON ((1.0197324444794666 3.019456289978678, "
        "0.999871987266061 5.013116389252246, 1.15 4.9, 2.85 4.9, 3.0000803010344903 5.013080440097467, "
        "2.9802682512317915 3.019456289978678, 1.0197324444794666 3.019456289978678)), POLYGON (("
        "3.019729727481788 3.0197290314268135, 2.9998719872660615 5.013116389252247, 3.149999999999999 4.9, "
        "4.9 4.9, 4.9 3.15, 5.013080440097467 2.9999196989655097, 3.019729727481788 3.0197290314268135)))"
    )
