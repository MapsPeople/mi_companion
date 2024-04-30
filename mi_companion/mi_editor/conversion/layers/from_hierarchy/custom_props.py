import logging
import math
from collections import defaultdict
from typing import Any, Mapping

# noinspection PyUnresolvedReferences
# from qgis.core.QgsVariantUtils import isNull, typeToDisplayString
import numpy

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QVariant

from mi_companion.configuration.constants import (
    ADD_FLOAT_NAN_CUSTOM_PROPERTY_VALUES,
    ADD_REAL_NONE_CUSTOM_PROPERTY_VALUES,
    ADD_STRING_NAN_CUSTOM_PROPERTY_VALUES,
    NAN_VALUE,
    NULL_VALUE,
    REAL_NONE_JSON_VALUE,
    STR_NA_VALUE,
)

logger = logging.getLogger(__name__)

__all__ = ["extract_custom_props"]


def extract_custom_props(
    layer_attributes: Mapping[str, Any]
) -> Mapping[str, Mapping[str, Any]]:
    """
    THIS IS THE DIRTIEST function ever written, null is a hell of a concept

    :param layer_attributes:
    :return:
    """
    custom_props = defaultdict(dict)
    for k, v in layer_attributes.items():
        if "custom_properties" in k:
            split_res = k.split(".")
            if len(split_res) >= 2:
                lang, cname = split_res[-2:]

                if isinstance(v, str):
                    v_str = v.lower().strip()
                    if (
                        (v_str == NAN_VALUE.lower())
                        or (v_str == NULL_VALUE.lower())
                        or (v_str == STR_NA_VALUE.lower())
                        # or len(v.strip()) == 0
                    ):
                        # logger.warning("Was PANDAS NULL STRING VALUE")
                        if ADD_STRING_NAN_CUSTOM_PROPERTY_VALUES:
                            custom_props[lang][cname] = None
                    else:
                        if v_str == REAL_NONE_JSON_VALUE.lower():
                            # logger.warning("Was REAL_NULL Value")
                            if ADD_REAL_NONE_CUSTOM_PROPERTY_VALUES:
                                custom_props[lang][cname] = None
                        else:
                            # logger.warning(f"Was str Value")
                            custom_props[lang][cname] = v
                elif isinstance(v, float):
                    if math.isnan(v) or numpy.isnan(v):
                        logger.warning(f"Was float Nan Value")
                        if ADD_FLOAT_NAN_CUSTOM_PROPERTY_VALUES:
                            custom_props[lang][cname] = None
                    else:
                        logger.warning(f"Was float Value")
                        custom_props[lang][cname] = v
                elif v is None:
                    logger.warning(f"{lang}.{cname} Was None Value")
                    custom_props[lang][cname] = "None"
                elif isinstance(v, QVariant):  # Handle this (qgis.core.NULL) aswell? #
                    # logger.warning(f"{typeToDisplayString(type(v))}")
                    if v.isNull():  # isNull(v):
                        logger.warning("Was null QVariant Value")
                        custom_props[lang][cname] = None
                    else:
                        logger.warning("Was QVariant Value")
                        custom_props[lang][cname] = v.value()
                else:
                    logger.warning(f"Was ({type(v)}) Value")
                    custom_props[lang][cname] = v
            else:
                logger.error(f"IGNORING {split_res}")

    return custom_props
