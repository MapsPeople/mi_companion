import logging
import uuid
from typing import Any, Collection, List, Optional

from jord.qgis_utilities.conversion.features import feature_to_shapely, parse_q_value

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QVariant

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

from integration_system.model import Category, LocationType, Solution
from mi_companion import DEFAULT_CUSTOM_PROPERTIES, VERBOSE
from mi_companion.configuration.options import read_bool_setting
from mi_companion.mi_editor.conversion.layers.from_hierarchy.custom_props import (
    extract_custom_props,
)
from mi_companion.mi_editor.conversion.layers.type_enums import BackendLocationTypeEnum
from mi_companion.qgis_utilities import is_str_value_null_like
from .extraction import extract_feature_attributes, extract_field_value, parse_field
from ...projection import prepare_geom_for_mi_db

__all__ = ["add_floor_contents"]

logger = logging.getLogger(__name__)


class MissingKeyColumn(Exception): ...


class MissingKeyValue(Exception): ...


def add_floor_locations(
    location_group_items: Any,
    solution: Solution,
    floor_key: str,
    backend_location_type: BackendLocationTypeEnum,
    collect_invalid: bool = False,
    collect_warnings: bool = False,
    collect_errors: bool = False,
    issues: Optional[List[str]] = None,
) -> None:
    """

    :param location_group_items:
    :param solution:
    :param floor_key:
    :param backend_location_type:
    :param collect_invalid:
    :param collect_warnings:
    :param collect_errors:
    :param issues:
    :return:
    """
    layer = location_group_items.layer()
    if layer:
        for layer_feature in layer.getFeatures():
            feature_attributes = extract_feature_attributes(layer_feature)

            location_type_admin_id = parse_field(
                feature_attributes, field_name="location_type"
            )

            location_type_key = LocationType.compute_key(
                admin_id=location_type_admin_id
            )
            if solution.location_types.get(location_type_key) is None:
                if read_bool_setting(
                    "ALLOW_LOCATION_TYPE_CREATION"
                ):  # TODO: MAKE CONFIRMATION DIALOG IF TRUE

                    try:
                        location_type_key = solution.add_location_type(
                            admin_id=location_type_admin_id, name=location_type_admin_id
                        )
                    except Exception as e:
                        _invalid = f"{location_type_admin_id=} is invalid {e}"
                        logger.error(_invalid)
                        if collect_invalid:
                            issues.append(_invalid)
                        else:
                            raise e

                else:
                    raise ValueError(
                        f"{location_type_key} is not a location type that already exists"
                    )

            custom_props = extract_custom_props(feature_attributes)

            if "admin_id" in feature_attributes:
                admin_id = feature_attributes["admin_id"]
                if admin_id is None:
                    raise MissingKeyValue(f"Missing key {admin_id=}")
                elif isinstance(admin_id, str):
                    v = admin_id
                    v_str = v.lower().strip()
                    if is_str_value_null_like(v_str):
                        raise MissingKeyColumn(f'Missing "admin_id" column')
                    else:
                        admin_id = v

                elif isinstance(admin_id, QVariant):
                    if admin_id.isNull():
                        raise MissingKeyValue(f"Missing key {admin_id=}")
                    else:
                        v = str(admin_id.value())

                        v_str = v.lower().strip()
                        if is_str_value_null_like(v_str):
                            raise MissingKeyColumn(f'Missing "admin_id" column')

                        admin_id = v
            else:
                raise MissingKeyColumn(f'Missing "admin_id" column')

            external_id = None
            if "external_id" in feature_attributes:
                external_id = feature_attributes["external_id"]
                if external_id is None:
                    if read_bool_setting("GENERATE_MISSING_EXTERNAL_IDS"):
                        external_id = uuid.uuid4().hex
                    else:
                        raise ValueError(
                            f"{layer_feature} is missing a valid external id"
                        )
                elif isinstance(external_id, str):
                    v = external_id
                    v_str = v.lower().strip()
                    if is_str_value_null_like(v_str):
                        external_id = None
                    else:
                        external_id = v

                elif isinstance(external_id, QVariant):
                    if external_id.isNull():
                        external_id = None
                    else:
                        v = str(external_id.value())

                        v_str = v.lower().strip()
                        if is_str_value_null_like(v_str):
                            external_id = None
                        else:
                            external_id = v

            name = None
            if "name" in feature_attributes:
                name = extract_field_value(feature_attributes, "name")

            description = None
            if "description" in feature_attributes:
                description = extract_field_value(feature_attributes, "description")

            is_active = None
            if "is_active" in feature_attributes:
                is_active = extract_field_value(feature_attributes, "is_active")
                if isinstance(is_active, str):
                    if is_active.lower().strip() == "false":
                        is_active = False
                    else:
                        is_active = True
                assert isinstance(is_active, bool), f"{type(is_active)}"

            is_searchable = None
            if "is_searchable" in feature_attributes:
                is_searchable = extract_field_value(feature_attributes, "is_searchable")
                if isinstance(is_searchable, str):
                    if is_searchable.lower().strip() == "false":
                        is_searchable = False
                    else:
                        is_searchable = True
                assert isinstance(is_searchable, bool), f"{type(is_searchable)}"

            if name is None:  # Fallback
                name = external_id

            if name is None:
                raise ValueError(f"{layer_feature} is missing a valid name")

            # TODO: IMPLEMENT POP UP CONFIRMATION OF DELETE FEATURE WHEN MISSING GEOMETRIES.

            location_geometry = feature_to_shapely(layer_feature)

            if location_geometry is None:
                logger.error(f"{location_geometry=}")

            if location_geometry is not None:
                common_kvs = dict(
                    admin_id=admin_id,
                    external_id=external_id,
                    name=name,
                    floor_key=floor_key,
                    is_active=is_active,
                    is_searchable=is_searchable,
                    location_type_key=location_type_key,
                    description=description,
                    custom_properties=(
                        custom_props if custom_props else DEFAULT_CUSTOM_PROPERTIES
                    ),
                )

                for k, v in feature_attributes.items():
                    if k not in common_kvs:
                        if k == "category_keys":
                            cat_keys = []
                            a = extract_field_value(feature_attributes, "category_keys")
                            if not isinstance(a, Collection):
                                logger.warning(f"Skipping {a} for {k}")
                                continue

                            for category_name in a:
                                if isinstance(category_name, str):
                                    if category_name.lower().strip() == "":
                                        continue

                                    category_key = Category.compute_key(
                                        name=category_name
                                    )
                                    if solution.categories.get(category_key) is None:
                                        if read_bool_setting(
                                            "ALLOW_CATEGORY_TYPE_CREATION"
                                        ):  # TODO: MAKE CONFIRMATION DIALOG IF TRUE
                                            try:
                                                category_key = solution.add_category(
                                                    category_name
                                                )
                                            except Exception as e:
                                                _invalid = (
                                                    f"{category_name=} is invalid {e}"
                                                )
                                                logger.error(_invalid)
                                                if collect_invalid:
                                                    issues.append(_invalid)
                                                else:
                                                    raise e
                                        else:
                                            raise ValueError(
                                                f"{category_key} is not a category that already exists"
                                            )
                                    cat_keys.append(category_key)
                                else:
                                    logger.error(
                                        f"Skipping invalid category {category_name} on {admin_id}"
                                    )

                            common_kvs["category_keys"] = cat_keys
                    else:
                        common_kvs[k] = extract_field_value(feature_attributes, k)

                shapely_geom = prepare_geom_for_mi_db(location_geometry)

                try:
                    if backend_location_type == BackendLocationTypeEnum.ROOM:
                        location_key = solution.add_room(
                            polygon=shapely_geom,
                            **common_kvs,
                        )
                    elif backend_location_type == BackendLocationTypeEnum.AREA:
                        location_key = solution.add_area(
                            polygon=shapely_geom,
                            **common_kvs,
                        )
                    elif backend_location_type == BackendLocationTypeEnum.POI:
                        location_key = solution.add_point_of_interest(
                            point=shapely_geom, **common_kvs
                        )
                    else:
                        raise Exception(f"{backend_location_type=} is unknown")

                    if VERBOSE:
                        logger.info(f"added {backend_location_type} {location_key}")
                except Exception as e:
                    _invalid = f"Invalid location: {e}"
                    logger.error(_invalid)
                    if collect_invalid:
                        issues.append(_invalid)
                    else:
                        raise e


def add_floor_contents(
    *,
    floor_group_items: QgsLayerTreeGroup,
    floor_key: str,
    solution: Solution,
    graph_key: Optional[str] = None,  # TODO: UNUSED
    floor_index: Optional[int] = None,  # TODO: UNUSED
    collect_invalid: bool = False,
    collect_warnings: bool = False,
    collect_errors: bool = False,
    issues: Optional[List[str]] = None,
) -> None:
    """

    :param floor_group_items:
    :param floor_key:
    :param solution:
    :param graph_key:
    :param floor_index:
    :param collect_invalid:
    :param collect_warnings:
    :param collect_errors:
    :param issues:
    :return:
    """
    for location_group_item in floor_group_items.children():
        if (
            isinstance(location_group_item, QgsLayerTreeLayer)
            and BackendLocationTypeEnum.ROOM.value in location_group_item.name()
            and floor_key is not None
        ):
            add_floor_locations(
                location_group_item,
                solution,
                floor_key,
                BackendLocationTypeEnum.ROOM,
                issues=issues,
                collect_invalid=collect_invalid,
                collect_warnings=collect_warnings,
                collect_errors=collect_errors,
            )

        if (
            isinstance(location_group_item, QgsLayerTreeLayer)
            and BackendLocationTypeEnum.POI.value in location_group_item.name()
            and floor_key is not None
        ):
            add_floor_locations(
                location_group_item,
                solution,
                floor_key,
                BackendLocationTypeEnum.POI,
                issues=issues,
                collect_invalid=collect_invalid,
                collect_warnings=collect_warnings,
                collect_errors=collect_errors,
            )

        if (
            isinstance(location_group_item, QgsLayerTreeLayer)
            and BackendLocationTypeEnum.AREA.value in location_group_item.name()
            and floor_key is not None
        ):
            add_floor_locations(
                location_group_item,
                solution,
                floor_key,
                BackendLocationTypeEnum.AREA,
                issues=issues,
                collect_invalid=collect_invalid,
                collect_warnings=collect_warnings,
                collect_errors=collect_errors,
            )
