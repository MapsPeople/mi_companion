import logging
import math
from collections import defaultdict
from typing import Any, Mapping, Optional

# noinspection PyUnresolvedReferences
# from qgis.core.QgsVariantUtils import isNull, typeToDisplayString
import numpy

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QVariant

from integration_system.model import DisplayRule
from mi_companion import (
    ADD_FLOAT_NAN_CUSTOM_PROPERTY_VALUES,
    ADD_REAL_NONE_CUSTOM_PROPERTY_VALUES,
    ADD_STRING_NAN_CUSTOM_PROPERTY_VALUES,
    REAL_NONE_JSON_VALUE,
)
from mi_companion.qgis_utilities import is_str_value_null_like

logger = logging.getLogger(__name__)

__all__ = ["extract_custom_props"]


def extract_custom_props(
    layer_attributes: Mapping[str, Any],
) -> Optional[Mapping[str, Mapping[str, Any]]]:
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
                    if is_str_value_null_like(v_str):
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
                    custom_props[lang][cname] = None
                elif isinstance(v, QVariant):  # Handle this (qgis.core.NULL) aswell? #
                    # logger.warning(f"{typeToDisplayString(type(v))}")
                    if v.isNull():  # isNull(v):
                        logger.warning("Was null QVariant Value")
                        custom_props[lang][cname] = None
                    else:
                        logger.warning("Was QVariant Value")
                        vs = v.value()
                        if isinstance(vs, str):
                            v_str_ = vs.lower().strip()
                            if is_str_value_null_like(v_str_):
                                # logger.warning("Was PANDAS NULL STRING VALUE")
                                if ADD_STRING_NAN_CUSTOM_PROPERTY_VALUES:
                                    custom_props[lang][cname] = None
                            else:
                                if v_str_ == REAL_NONE_JSON_VALUE.lower():
                                    # logger.warning("Was REAL_NULL Value")
                                    if ADD_REAL_NONE_CUSTOM_PROPERTY_VALUES:
                                        custom_props[lang][cname] = None
                                else:
                                    # logger.warning(f"Was str Value")
                                    custom_props[lang][cname] = vs
                        else:
                            logger.warning(f"Was ({type(vs)}) Value")
                            custom_props[lang][cname] = vs
                else:
                    logger.warning(f"Was ({type(v)}) Value")
                    custom_props[lang][cname] = v
            else:
                logger.error(f"IGNORING {split_res}")

    if len(custom_props) == 0:
        return None

    return custom_props


def extract_display_rule(
    layer_attributes: Mapping[str, Any],
) -> DisplayRule:
    """Extract display rule from layer attributes.

    Args:
        layer_attributes: Dictionary of layer attributes containing display settings

    Returns:
        DisplayRule if valid display attributes found, None otherwise
    """
    # Early return if no attributes
    if not layer_attributes:
        return None

    display_attrs = {}

    # Map of display rule field names and their types
    field_types = {
        "zoom_from": float,
        "zoom_to": float,
        "label_zoom_from": float,
        "label_zoom_to": float,
        "visible": bool,
        "icon": str,
        "icon_visible": bool,
        "icon_placement": str,
        "badge": str,
        "polygon": bool,
        "extrusion": bool,
        "walls": bool,
        "model3d": str,
        "model2d": str,
        "label": str,
        "label_visible": bool,
        "label_style": str,
        "label_type": str,
        "image_scale": float,
        "image_size": float,
        "marker_elevation": float,
    }

    # Extract display rule fields from attributes
    for attr_name, attr_value in layer_attributes.items():
        # Check if attribute name starts with display_rule
        if attr_name.startswith("display_rule."):
            field_name = attr_name.split(".")[-1]
            if field_name in field_types:
                # Handle QVariant values
                if isinstance(attr_value, QVariant):
                    if attr_value.isNull():
                        continue
                    attr_value = attr_value.value()

                # Skip null-like string values
                if isinstance(attr_value, str) and is_str_value_null_like(
                    attr_value.lower().strip()
                ):
                    continue

                # Convert to expected type
                try:
                    display_attrs[field_name] = field_types[field_name](attr_value)
                except (ValueError, TypeError):
                    logger.warning(
                        f"Could not convert {attr_name}={attr_value} to {field_types[field_name]}"
                    )
                    continue

    # Return None if no valid display attributes found
    if not display_attrs:
        return None

    # Create DisplayRule with extracted attributes
    try:
        return DisplayRule(**display_attrs)
    except Exception as e:
        logger.error(f"Failed to create DisplayRule: {e}")
        return None
