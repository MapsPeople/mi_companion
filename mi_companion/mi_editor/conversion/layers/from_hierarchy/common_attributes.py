import logging
import math
from collections import defaultdict
from typing import Any, Mapping, Optional

# noinspection PyUnresolvedReferences
# from qgis.core.QgsVariantUtils import isNull, typeToDisplayString
import numpy

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QVariant

from integration_system.tools.common_models import (
    MIIconPlacementRuleEnum,
    MILabelTypeOptionEnum,
)
from integration_system.model import (
    BadgeDisplayRule,
    Data3D,
    DisplayPolygon,
    DisplayRule,
    ImageSize,
    LabelDisplayRule,
    Model2d,
    Model3d,
    OptionalDisplayRule,
)
from mi_companion import (
    ADD_FLOAT_NAN_CUSTOM_PROPERTY_VALUES,
    ADD_REAL_NONE_CUSTOM_PROPERTY_VALUES,
    ADD_STRING_NAN_CUSTOM_PROPERTY_VALUES,
    REAL_NONE_JSON_VALUE,
)
from mi_companion.qgis_utilities import is_str_value_null_like

logger = logging.getLogger(__name__)

__all__ = [
    "extract_two_level_str_map",
    "extract_single_level_str_map",
    "extract_display_rule",
]


def extract_two_level_str_map(
    layer_attributes: Mapping[str, Any],
    *,
    nested_str_map_field_name: str = "custom_properties",
) -> Optional[Mapping[str, Mapping[str, Any]]]:
    """
    THIS IS THE DIRTIEST function ever written; null is a hell of a concept

    :param nested_str_map_field_name:
    :param layer_attributes:
    :return:
    """
    custom_props = defaultdict(dict)
    for k, v in layer_attributes.items():
        if nested_str_map_field_name in k:
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


def extract_single_level_str_map(
    layer_attributes: Mapping[str, Any],
    *,
    nested_str_map_field_name: str = "fields",
) -> Optional[Mapping[str, Optional[Any]]]:
    """
    THIS IS THE DIRTIEST function ever written; null is a hell of a concept

    :param nested_str_map_field_name:
    :param layer_attributes:
    :return:
    """
    custom_props = {}
    for k, v in layer_attributes.items():
        if nested_str_map_field_name in k:
            split_res = k.split(".")
            if len(split_res) == 2:
                cname = split_res[-1]

                if isinstance(v, str):
                    v_str = v.lower().strip()
                    if is_str_value_null_like(v_str):
                        # logger.warning("Was PANDAS NULL STRING VALUE")
                        if ADD_STRING_NAN_CUSTOM_PROPERTY_VALUES:
                            custom_props[cname] = None
                    else:
                        if v_str == REAL_NONE_JSON_VALUE.lower():
                            # logger.warning("Was REAL_NULL Value")
                            if ADD_REAL_NONE_CUSTOM_PROPERTY_VALUES:
                                custom_props[cname] = None
                        else:
                            # logger.warning(f"Was str Value")
                            custom_props[cname] = v
                elif isinstance(v, float):
                    if math.isnan(v) or numpy.isnan(v):
                        logger.warning(f"Was float Nan Value")
                        if ADD_FLOAT_NAN_CUSTOM_PROPERTY_VALUES:
                            custom_props[cname] = None
                    else:
                        logger.warning(f"Was float Value")
                        custom_props[cname] = v
                elif v is None:
                    logger.warning(f"{cname} Was None Value")
                    custom_props[cname] = None
                elif isinstance(v, QVariant):  # Handle this (qgis.core.NULL) aswell? #
                    # logger.warning(f"{typeToDisplayString(type(v))}")
                    if v.isNull():  # isNull(v):
                        logger.warning("Was null QVariant Value")
                        custom_props[cname] = None
                    else:
                        logger.warning("Was QVariant Value")
                        vs = v.value()
                        if isinstance(vs, str):
                            v_str_ = vs.lower().strip()
                            if is_str_value_null_like(v_str_):
                                # logger.warning("Was PANDAS NULL STRING VALUE")
                                if ADD_STRING_NAN_CUSTOM_PROPERTY_VALUES:
                                    custom_props[cname] = None
                            else:
                                if v_str_ == REAL_NONE_JSON_VALUE.lower():
                                    # logger.warning("Was REAL_NULL Value")
                                    if ADD_REAL_NONE_CUSTOM_PROPERTY_VALUES:
                                        custom_props[cname] = None
                                else:
                                    # logger.warning(f"Was str Value")
                                    custom_props[cname] = vs
                        else:
                            logger.warning(f"Was ({type(vs)}) Value")
                            custom_props[cname] = vs
                else:
                    logger.warning(f"Was ({type(v)}) Value")
                    custom_props[cname] = v
            else:
                logger.error(f"IGNORING {split_res}")

    if len(custom_props) == 0:
        return None

    return custom_props


def extract_display_rule(
    layer_attributes: Mapping[str, Any],
) -> OptionalDisplayRule:
    """Extract display rule from layer attributes.

    Args:
        layer_attributes: Dictionary of layer attributes containing display settings

    Returns:
        DisplayRule if valid display attributes found, None otherwise
    """
    if not layer_attributes:
        return None

    display_rule_attrs = {}

    # Field types based on DisplayRule class definition
    field_types = {
        "zoom_from": int,
        "zoom_to": int,
        "label_zoom_from": int,
        "label_zoom_to": int,
        "visible": bool,
        "icon": str,
        "icon_visible": bool,
        "icon_placement": MIIconPlacementRuleEnum,
        "badge": BadgeDisplayRule,
        "polygon": DisplayPolygon,
        "extrusion": Data3D,
        "walls": Data3D,
        "model3d": Model3d,
        "model2d": Model2d,
        "label": str,
        "label_visible": bool,
        "label_style": LabelDisplayRule,
        "label_type": MILabelTypeOptionEnum,
        "image_scale": float,
        "image_size": ImageSize,
        "marker_elevation": float,
    }

    # Extract nested object fields
    nested_types = {
        BadgeDisplayRule,
        DisplayPolygon,
        Data3D,
        Model3d,
        Model2d,
        LabelDisplayRule,
        ImageSize,
    }

    for attr_name, attr_value in layer_attributes.items():
        if attr_name.startswith("display_rule."):
            parts = attr_name.split(".")

            _, field_name, *rest = parts

            if field_name in field_types:
                field_type = field_types[field_name]

                # Handle QVariant
                if isinstance(attr_value, QVariant):
                    if attr_value.isNull():
                        continue

                    attr_value = attr_value.value()

                # Skip null-like strings
                if isinstance(attr_value, str) and is_str_value_null_like(
                    attr_value.lower().strip()
                ):
                    continue

                try:
                    # Handle nested objects
                    if field_type in nested_types:
                        if rest:
                            # Initialize nested dict if needed
                            if field_name not in display_rule_attrs:
                                display_rule_attrs[field_name] = {}

                            if len(rest) > 1:
                                logger.error(
                                    f"A unexpected rest was found {rest} for {attr_name}={attr_value} for {field_name}="
                                    f"{field_type}"
                                )
                                continue

                            nested_field = rest[0]
                            display_rule_attrs[field_name][nested_field] = attr_value
                        else:
                            if True:
                                logger.warning(
                                    f"Ignoring {attr_name}={attr_value} for {field_name}={field_type}"
                                )
                                continue
                    else:
                        # Handle enums
                        if field_type in (
                            MIIconPlacementRuleEnum,
                            MILabelTypeOptionEnum,
                        ):
                            display_rule_attrs[field_name] = field_type(attr_value)
                        elif field_type is int:
                            display_rule_attrs[field_name] = int(float(attr_value))
                        elif field_type is float:
                            display_rule_attrs[field_name] = float(attr_value)
                        else:
                            display_rule_attrs[field_name] = field_type(attr_value)

                except (ValueError, TypeError) as e:
                    logger.warning(
                        f"Could not convert {attr_name}={attr_value} to {field_type}: {e}"
                    )
                    continue

    if not display_rule_attrs:
        return None

    try:
        return DisplayRule(**display_rule_attrs)
    except Exception as e:
        logger.error(f"Failed to create DisplayRule: {e}")
        return None
