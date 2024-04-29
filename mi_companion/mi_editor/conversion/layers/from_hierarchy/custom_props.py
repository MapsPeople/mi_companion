import logging
import math
from collections import defaultdict

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
)

logger = logging.getLogger(__name__)

__all__ = ["extract_custom_props"]


def extract_custom_props(layer_attributes):
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
                        # or len(v.strip()) == 0
                    ):
                        if ADD_STRING_NAN_CUSTOM_PROPERTY_VALUES:
                            custom_props[lang][cname] = None
                    else:
                        if v_str == REAL_NONE_JSON_VALUE.lower():
                            if ADD_REAL_NONE_CUSTOM_PROPERTY_VALUES:
                                custom_props[lang][cname] = None
                        else:
                            custom_props[lang][cname] = v
                elif isinstance(v, float):
                    if math.isnan(v) or numpy.isnan(v):
                        if ADD_FLOAT_NAN_CUSTOM_PROPERTY_VALUES:
                            custom_props[lang][cname] = None
                    else:
                        custom_props[lang][cname] = v
                elif v is None:
                    custom_props[lang][cname] = None
                elif isinstance(v, QVariant):  # Handle this (qgis.core.NULL) aswell? #
                    # logger.warning(f"{typeToDisplayString(type(v))}")
                    if v.isNull():  # isNull(v):
                        custom_props[lang][cname] = None
                    else:
                        custom_props[lang][cname] = v.value()
                else:
                    custom_props[lang][cname] = v
    return custom_props
