import logging
import math
from typing import Any, Iterable, Mapping, Optional

# noinspection PyUnresolvedReferences
# from qgis.core.QgsVariantUtils import isNull, typeToDisplayString
import numpy

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QVariant

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtGui import QColor

from jord.qgis_utilities import (
    REAL_NONE_JSON_VALUE,
    is_str_value_null_like,
    parse_q_value,
)
from mi_companion import (
    ADD_FLOAT_NAN_TRANSLATION_VALUES,
    ADD_REAL_NONE_TRANSLATION_VALUES,
    ADD_STRING_NAN_TRANSLATION_VALUES,
)
from sync_module.mi import MI_OUTSIDE_BUILDING_NAME
from sync_module.model import (
    BadgeDisplayRule,
    Data3D,
    DisplayPolygon,
    DisplayRule,
    ImageSize,
    LabelDisplayRule,
    Model2d,
    Model3d,
    OptionalDisplayRule,
    StreetViewConfig,
)
from sync_module.shared import (
    LanguageBundle,
    MIIconPlacementRuleEnum,
    MILabelTypeOptionEnum,
)
from warg import nested_dict, str_to_bool

logger = logging.getLogger(__name__)

__all__ = [
    "extract_translations",
    "extract_single_level_str_map",
    "extract_display_rule",
    "parse_q_value_field_translations",
    "extract_street_view_config",
]


RETURN_EMPTY_DISPLAY_RULE = False
PATCH_MISSING_TRANSLATIONS = True


class MissingTranslationsException(Exception):
    pass


def extract_translations(
    layer_attributes: Mapping[str, Any],
    *,
    required_languages: Iterable[str],
    nested_str_map_field_name: str = "translations",
) -> Optional[Mapping[str, LanguageBundle]]:
    """
    THIS IS THE DIRTIEST function ever written; null is a hell of a concept

    :param required_languages:
    :param nested_str_map_field_name:
    :param layer_attributes:
    :return:
    """
    translations = nested_dict()
    for k, v in layer_attributes.items():
        if nested_str_map_field_name in k:
            split_res = k.split(".")
            if len(split_res) == 3:
                lang, cname = split_res[-2:]

                parse_q_value_translations(cname, lang, translations, v)
            elif len(split_res) == 4:
                lang, cname, f_name = split_res[-3:]
                parse_q_value_field_translations(cname, f_name, lang, translations, v)
            else:
                logger.error(f"IGNORING {split_res}")

    if len(translations) == 0:
        return None

    out = {}
    for language, v in translations.items():
        out[language] = LanguageBundle(
            name=v["name"] if "name" in v else None,
            description=v["description"] if "description" in v else None,
            fields=v["fields"] if "fields" in v else None,
        )

    missing_translations = set(required_languages) - set(translations.keys())
    if PATCH_MISSING_TRANSLATIONS:
        if "en" not in out:
            if True:
                raise Exception('Big problem! The "en".name not in translations')
            else:
                ...
                # TODO: DEFAULT TO LOCATION_TYPE?

        if not out["en"].name.lower().startswith(MI_OUTSIDE_BUILDING_NAME.lower()):
            for language in missing_translations:
                logger.warning(f"Patching {language} translation with {out['en']}")
                out[language] = out["en"]
    else:
        raise MissingTranslationsException(
            f"Missing translations for languages {missing_translations}"
        )

    return out


def extract_street_view_config(
    layer_attributes: Mapping[str, Any],
    *,
    nested_str_map_field_name: str = "street_view_config",
) -> Optional[StreetViewConfig]:
    """
    THIS IS THE DIRTIEST function ever written; null is a hell of a concept

    :param nested_str_map_field_name:
    :param layer_attributes:
    :return:
    """

    args = {}
    for k, v in layer_attributes.items():
        if nested_str_map_field_name in k:
            split_res = k.split(".")
            if len(split_res) == 2:
                field_name = split_res[-1]

                val = parse_q_value(v)

                if val is None:
                    continue

                args[field_name] = val
            else:
                logger.error(f"IGNORING {split_res}")

    if len(args) == 0:
        return None

    return StreetViewConfig(**args)


def parse_q_value_field_translations(cname, f_name, lang, translations, v):
    if isinstance(v, str):
        v_str = v.lower().strip()
        if is_str_value_null_like(v_str):
            # logger.debug("Was PANDAS NULL STRING VALUE")
            if ADD_STRING_NAN_TRANSLATION_VALUES:
                translations[lang][cname][f_name] = None
        else:
            if v_str == REAL_NONE_JSON_VALUE.lower():
                # logger.debug("Was REAL_NULL Value")
                if ADD_REAL_NONE_TRANSLATION_VALUES:
                    translations[lang][cname][f_name] = None
            else:
                # logger.debug(f"Was str Value")
                translations[lang][cname][f_name] = v
    elif isinstance(v, float):
        if math.isnan(v) or numpy.isnan(v):
            logger.debug(f"Was float Nan Value")
            if ADD_FLOAT_NAN_TRANSLATION_VALUES:
                translations[lang][cname][f_name] = None
        else:
            logger.debug(f"Was float Value")
            translations[lang][cname][f_name] = v
    elif v is None:
        logger.debug(f"{lang}.{cname} Was None Value")
        translations[lang][cname][f_name] = None
    elif isinstance(v, QVariant):  # Handle this (qgis.core.NULL) aswell? #
        # logger.debug(f"{typeToDisplayString(type(v))}")
        if v.isNull():  # isNull(v):
            logger.debug("Was null QVariant Value")
            translations[lang][cname][f_name] = None
        else:
            logger.debug("Was QVariant Value")
            vs = v.value()
            if isinstance(vs, str):
                v_str_ = vs.lower().strip()
                if is_str_value_null_like(v_str_):
                    # logger.debug("Was PANDAS NULL STRING VALUE")
                    if ADD_STRING_NAN_TRANSLATION_VALUES:
                        translations[lang][cname][f_name] = None
                else:
                    if v_str_ == REAL_NONE_JSON_VALUE.lower():
                        # logger.debug("Was REAL_NULL Value")
                        if ADD_REAL_NONE_TRANSLATION_VALUES:
                            translations[lang][cname][f_name] = None
                    else:
                        # logger.debug(f"Was str Value")
                        translations[lang][cname][f_name] = vs
            else:
                logger.debug(f"Was ({type(vs)}) Value")
                translations[lang][cname][f_name] = vs
    else:
        logger.debug(f"Was ({type(v)}) Value")
        translations[lang][cname][f_name] = v


def parse_q_value_translations(cname, lang, translations, v):
    if isinstance(v, str):
        v_str = v.lower().strip()
        if is_str_value_null_like(v_str):
            # logger.debug("Was PANDAS NULL STRING VALUE")
            if ADD_STRING_NAN_TRANSLATION_VALUES:
                translations[lang][cname] = None
        else:
            if v_str == REAL_NONE_JSON_VALUE.lower():
                # logger.debug("Was REAL_NULL Value")
                if ADD_REAL_NONE_TRANSLATION_VALUES:
                    translations[lang][cname] = None
            else:
                # logger.debug(f"Was str Value")
                translations[lang][cname] = v
    elif isinstance(v, float):
        if math.isnan(v) or numpy.isnan(v):
            logger.debug(f"Was float Nan Value")
            if ADD_FLOAT_NAN_TRANSLATION_VALUES:
                translations[lang][cname] = None
        else:
            logger.debug(f"Was float Value")
            translations[lang][cname] = v
    elif v is None:
        logger.debug(f"{lang}.{cname} Was None Value")
        translations[lang][cname] = None
    elif isinstance(v, QVariant):  # Handle this (qgis.core.NULL) aswell? #
        # logger.debug(f"{typeToDisplayString(type(v))}")
        if v.isNull():  # isNull(v):
            logger.debug("Was null QVariant Value")
            translations[lang][cname] = None
        else:
            logger.debug("Was QVariant Value")
            vs = v.value()
            if isinstance(vs, str):
                v_str_ = vs.lower().strip()
                if is_str_value_null_like(v_str_):
                    # logger.debug("Was PANDAS NULL STRING VALUE")
                    if ADD_STRING_NAN_TRANSLATION_VALUES:
                        translations[lang][cname] = None
                else:
                    if v_str_ == REAL_NONE_JSON_VALUE.lower():
                        # logger.debug("Was REAL_NULL Value")
                        if ADD_REAL_NONE_TRANSLATION_VALUES:
                            translations[lang][cname] = None
                    else:
                        # logger.debug(f"Was str Value")
                        translations[lang][cname] = vs
            else:
                logger.debug(f"Was ({type(vs)}) Value")
                translations[lang][cname] = vs
    else:
        logger.debug(f"Was ({type(v)}) Value")
        translations[lang][cname] = v


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
                        # logger.debug("Was PANDAS NULL STRING VALUE")
                        if ADD_STRING_NAN_TRANSLATION_VALUES:
                            custom_props[cname] = None
                    else:
                        if v_str == REAL_NONE_JSON_VALUE.lower():
                            # logger.debug("Was REAL_NULL Value")
                            if ADD_REAL_NONE_TRANSLATION_VALUES:
                                custom_props[cname] = None
                        else:
                            # logger.debug(f"Was str Value")
                            custom_props[cname] = v
                elif isinstance(v, float):
                    if math.isnan(v) or numpy.isnan(v):
                        logger.debug(f"Was float Nan Value")
                        if ADD_FLOAT_NAN_TRANSLATION_VALUES:
                            custom_props[cname] = None
                    else:
                        logger.debug(f"Was float Value")
                        custom_props[cname] = v
                elif v is None:
                    logger.debug(f"{cname} Was None Value")
                    custom_props[cname] = None
                elif isinstance(v, QVariant):  # Handle this (qgis.core.NULL) aswell? #
                    # logger.debug(f"{typeToDisplayString(type(v))}")
                    if v.isNull():  # isNull(v):
                        logger.debug("Was null QVariant Value")
                        custom_props[cname] = None
                    else:
                        logger.debug("Was QVariant Value")
                        vs = v.value()
                        if isinstance(vs, str):
                            v_str_ = vs.lower().strip()
                            if is_str_value_null_like(v_str_):
                                # logger.debug("Was PANDAS NULL STRING VALUE")
                                if ADD_STRING_NAN_TRANSLATION_VALUES:
                                    custom_props[cname] = None
                            else:
                                if v_str_ == REAL_NONE_JSON_VALUE.lower():
                                    # logger.debug("Was REAL_NULL Value")
                                    if ADD_REAL_NONE_TRANSLATION_VALUES:
                                        custom_props[cname] = None
                                else:
                                    # logger.debug(f"Was str Value")
                                    custom_props[cname] = vs
                        else:
                            logger.debug(f"Was ({type(vs)}) Value")
                            custom_props[cname] = vs
                else:
                    logger.debug(f"Was ({type(v)}) Value")
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
        if RETURN_EMPTY_DISPLAY_RULE:
            return DisplayRule()

        return None

    display_rule_attrs = {}

    # Field types based on DisplayRule class definition
    field_types = {
        "zoom_from": int,
        "zoom_to": int,
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
        "label_zoom_from": int,
        "label_zoom_to": int,
        "label_type": MILabelTypeOptionEnum,
        "label_max_width": int,
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

                if isinstance(attr_value, QColor):
                    attr_name = attr_value.name()

                elif isinstance(attr_value, QVariant):
                    if attr_value.isNull():
                        continue

                    attr_value = attr_value.value()

                if attr_value is None:
                    continue

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

                            # if nested_field == 'label_visible':
                            #  attr_value = str_to_bool(attr_value)

                            display_rule_attrs[field_name][nested_field] = attr_value
                        else:
                            if True:
                                logger.debug(
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
                        elif field_type is bool:
                            display_rule_attrs[field_name] = str_to_bool(attr_value)
                        else:
                            display_rule_attrs[field_name] = field_type(attr_value)

                except (ValueError, TypeError) as e:
                    logger.warning(
                        f"Could not convert {attr_name}={attr_value} to {field_type}: {e}"
                    )
                    continue

    if not display_rule_attrs:
        if RETURN_EMPTY_DISPLAY_RULE:
            return DisplayRule()

        return None

    try:
        return DisplayRule(**display_rule_attrs)
    except Exception as e:
        logger.error(f"Failed to create DisplayRule: {e}")
        if RETURN_EMPTY_DISPLAY_RULE:
            return DisplayRule()

        return None
