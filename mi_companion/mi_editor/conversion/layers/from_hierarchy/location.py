import logging
import uuid
from typing import Any, Collection, Mapping, Optional

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

from integration_system.model import Category, LocationType, Solution
from mi_companion import DEFAULT_CUSTOM_PROPERTIES, VERBOSE
from mi_companion.configuration.options import read_bool_setting
from mi_companion.mi_editor.conversion.layers.from_hierarchy.custom_props import (
    extract_custom_props,
)
from mi_companion.mi_editor.conversion.layers.from_hierarchy.extraction import (
    feature_to_shapely,
)
from mi_companion.mi_editor.conversion.layers.type_enums import LocationTypeEnum

__all__ = ["add_floor_contents"]

from mi_companion.mi_editor.conversion.projection import prepare_geom_for_mi_db
from mi_companion.utilities.string_parsing import is_str_value_null_like

logger = logging.getLogger(__name__)
# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QVariant


class MissingKeyColumn(Exception): ...


class MissingKeyValue(Exception): ...


def add_floor_locations(
    location_group_items: Any,
    solution: Solution,
    floor_key: str,
    location_type: LocationTypeEnum,
) -> None:
    layer = location_group_items.layer()
    if layer:
        for layer_feature in layer.getFeatures():
            feature_attributes = {
                k.name(): v
                for k, v in zip(
                    layer_feature.fields(),
                    layer_feature.attributes(),
                )
            }

            location_type_name = feature_attributes["location_type.name"]
            if isinstance(location_type_name, str):
                ...
            elif isinstance(location_type_name, QVariant):
                # logger.warning(f"{typeToDisplayString(type(v))}")
                if location_type_name.isNull():  # isNull(v):
                    location_type_name = None
                else:
                    location_type_name = location_type_name.value()

            location_type_key = LocationType.compute_key(name=location_type_name)
            if solution.location_types.get(location_type_key) is None:
                if read_bool_setting(
                    "ALLOW_LOCATION_TYPE_CREATION"
                ):  # TODO: MAKE CONFIRMATION DIALOG IF TRUE
                    location_type_key = solution.add_location_type(location_type_name)
                else:
                    raise ValueError(
                        f"{location_type_key} is not a valid location type"
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

            is_searchable = None
            if "is_searchable" in feature_attributes:
                is_searchable = extract_field_value(feature_attributes, "is_searchable")
                if isinstance(is_searchable, str):
                    if is_searchable.lower().strip() == "false":
                        is_searchable = False
                    else:
                        is_searchable = True

            if name is None:  # Fallback
                name = external_id

            if name is None:
                raise ValueError(f"{layer_feature} is missing a valid name")

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
                            a = feature_attributes["category_keys"]
                            if not isinstance(a, Collection):
                                logger.warning(f"Skipping {a} for {k}")
                                continue

                            for category_name in a:
                                if isinstance(category_name, str):
                                    category_key = Category.compute_key(
                                        name=category_name
                                    )
                                    if solution.categories.get(category_key) is None:
                                        if read_bool_setting(
                                            "ALLOW_CATEGORY_TYPE_CREATION"
                                        ):  # TODO: MAKE CONFIRMATION DIALOG IF TRUE
                                            category_key = solution.add_category(
                                                category_name
                                            )
                                        else:
                                            raise ValueError(
                                                f"{category_key} is not a valid category"
                                            )
                                    cat_keys.append(category_key)

                            common_kvs["category_keys"] = cat_keys
                    else:
                        common_kvs[k] = extract_field_value(feature_attributes, k)

                shapely_geom = prepare_geom_for_mi_db(location_geometry)

                if location_type == LocationTypeEnum.ROOM:
                    room_key = solution.add_room(
                        polygon=shapely_geom,
                        **common_kvs,
                    )
                elif location_type == LocationTypeEnum.AREA:
                    room_key = solution.add_area(
                        polygon=shapely_geom,
                        **common_kvs,
                    )
                elif location_type == LocationTypeEnum.POI:
                    room_key = solution.add_point_of_interest(
                        point=shapely_geom, **common_kvs
                    )
                else:
                    raise Exception(f"{location_type=} is unknown")
                if VERBOSE:
                    logger.info(f"added {location_type} {room_key}")


def extract_field_value(feature_attributes: Mapping[str, Any], field_name: str) -> Any:
    field_value = feature_attributes[field_name]
    if field_value is None:
        ...
    elif isinstance(field_value, str):
        v = field_value
        v_str = v.lower().strip()
        if is_str_value_null_like(v_str):
            field_value = None
        else:
            field_value = v
    elif isinstance(field_value, QVariant):
        if field_value.isNull():
            field_value = None
        else:
            v = str(field_value.value())

            v_str = v.lower().strip()
            if is_str_value_null_like(v_str):
                field_value = None
            else:
                field_value = v

    return field_value


def add_floor_contents(
    *,
    floor_group_items: QgsLayerTreeGroup,
    floor_key: str,
    solution: Solution,
    graph_key: Optional[str] = None,  # TODO: UNUSED
    floor_index: Optional[int] = None,  # TODO: UNUSED
) -> None:
    for location_group_item in floor_group_items.children():
        if (
            isinstance(location_group_item, QgsLayerTreeLayer)
            and LocationTypeEnum.ROOM.value in location_group_item.name()
            and floor_key is not None
        ):
            add_floor_locations(
                location_group_item, solution, floor_key, LocationTypeEnum.ROOM
            )

        if (
            isinstance(location_group_item, QgsLayerTreeLayer)
            and LocationTypeEnum.POI.value in location_group_item.name()
            and floor_key is not None
        ):
            add_floor_locations(
                location_group_item, solution, floor_key, LocationTypeEnum.POI
            )

        if (
            isinstance(location_group_item, QgsLayerTreeLayer)
            and LocationTypeEnum.AREA.value in location_group_item.name()
            and floor_key is not None
        ):
            add_floor_locations(
                location_group_item, solution, floor_key, LocationTypeEnum.AREA
            )
