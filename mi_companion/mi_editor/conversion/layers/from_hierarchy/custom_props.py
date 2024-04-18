import math
from collections import defaultdict

import numpy

from mi_companion.configuration.constants import (
    NAN_VALUE,
    NULL_VALUE,
    ADD_FLOAT_NAN_CUSTOM_PROPERTY_VALUES,
    ADD_STRING_NAN_CUSTOM_PROPERTY_VALUES,
    REAL_NONE_JSON_VALUE,
    ADD_REAL_NONE_CUSTOM_PROPERTY_VALUES,
)


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
                else:
                    custom_props[lang][cname] = v
    return custom_props
