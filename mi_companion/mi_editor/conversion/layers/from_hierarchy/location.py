import ast

# noinspection PyUnresolvedReferences
import datetime
import logging
import uuid
from typing import Any, Collection, List, Optional

import shapely

# noinspection PyUnresolvedReferences
# noinspection PyUnresolvedReferences
# noinspection PyUnresolvedReferences
from qgis.PyQt import QtCore, QtGui, QtWidgets, QtWidgets, QtWidgets

# noinspection PyUnresolvedReferences
# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QVariant, QVariant

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtWidgets import QMessageBox, QTextEdit

# noinspection PyUnresolvedReferences
# noinspection PyUnresolvedReferences
from qgis.core import (
    QgsLayerTreeGroup,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsLayerTreeLayer,
    QgsProject,
    QgsProject,
)

from integration_system.model import (
    Category,
    LocationType,
    OpeningHoursDetail,
    Solution,
    StrToDetailTypeMap,
)
from integration_system.model.typings import LanguageBundle
from integration_system.tools.serialisation import standard_opening_hours_from_dict
from jord.qgis_utilities import (
    extract_feature_attributes,
    extract_field_value,
    feature_to_shapely,
    is_str_value_null_like,
    parse_field,
    qgs_geometry_to_shapely,
)
from mi_companion import (
    ANCHOR_AS_INDIVIDUAL_FIELDS,
    VERBOSE,
)
from mi_companion.configuration.options import read_bool_setting
from mi_companion.mi_editor.conversion.layers.from_hierarchy.common_attributes import (
    extract_display_rule,
    extract_street_view_config,
    extract_translations,
)
from mi_companion.mi_editor.conversion.layers.type_enums import BackendLocationTypeEnum
from mi_companion.mi_editor.hierarchy.validation_dialog_utilities import (
    make_hierarchy_validation_dialog,
)
from warg import str_to_bool
from .constants import APPENDIX_INVALID_GEOMETRY_DIALOG_MESSAGE
from mi_companion.mi_editor.conversion.projection import prepare_geom_for_mi_db_qgis

__all__ = ["add_floor_contents"]

logger = logging.getLogger(__name__)


class MissingKeyColumn(Exception): ...


class MissingKeyValue(Exception): ...


def add_floor_locations(
    location_group_item: Any,
    solution: Solution,
    floor_key: str,
    backend_location_type: BackendLocationTypeEnum,
    collect_invalid: bool = False,
    collect_warnings: bool = False,
    collect_errors: bool = False,
    issues: Optional[List[str]] = None,
) -> None:
    """

    :param location_group_item:
    :param solution:
    :param floor_key:
    :param backend_location_type:
    :param collect_invalid:
    :param collect_warnings:
    :param collect_errors:
    :param issues:
    :return:
    """
    layer = location_group_item.layer()
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
                            admin_id=location_type_admin_id,
                            translations={
                                "en": LanguageBundle(name=location_type_admin_id)
                            },
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

            translations = extract_translations(feature_attributes)

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

            restrictions = None
            if "restrictions" in feature_attributes:
                restrictions = extract_field_value(feature_attributes, "restrictions")

                if not restrictions:
                    restrictions = None

            is_obstacle = None
            if "is_obstacle" in feature_attributes:
                is_obstacle = extract_field_value(feature_attributes, "is_obstacle")
                feature_attributes.pop("is_obstacle")

                if is_obstacle is not None:
                    if not isinstance(is_obstacle, bool):
                        is_obstacle = str_to_bool(is_obstacle)

            is_selectable = None
            if "is_selectable" in feature_attributes:
                is_selectable = extract_field_value(feature_attributes, "is_selectable")
                feature_attributes.pop("is_selectable")

                if is_selectable is not None:
                    if not isinstance(is_selectable, bool):
                        is_selectable = str_to_bool(is_selectable)

            settings_3d_width = None
            if "settings_3d_width" in feature_attributes:
                settings_3d_width = extract_field_value(
                    feature_attributes, "settings_3d_width"
                )
                feature_attributes.pop("settings_3d_width")

            settings_3d_margin = None
            if "settings_3d_margin" in feature_attributes:
                settings_3d_margin = extract_field_value(
                    feature_attributes, "settings_3d_margin"
                )
                feature_attributes.pop("settings_3d_margin")

            active_to = None
            if "active_to" in feature_attributes:  # TODO: CONVERT THIS
                active_to = extract_field_value(feature_attributes, "active_to")
                feature_attributes.pop("active_to")

            active_from = None
            if "active_from" in feature_attributes:  # TODO: CONVERT THIS
                active_from = extract_field_value(feature_attributes, "active_from")
                feature_attributes.pop("active_from")

            street_view_config = extract_street_view_config(feature_attributes)

            try:
                location_geometry = feature_to_shapely(layer_feature)
            except Exception as e:
                reply = make_hierarchy_validation_dialog(
                    "Invalid Location Feature Detected",
                    f"The Location feature with Admin ID '{admin_id}' located in '{location_group_item.name()}' has "
                    f"an invalid "
                    f"geometry.\n\n"
                    # f"\n__________________{e}\n__________________\n"
                    + APPENDIX_INVALID_GEOMETRY_DIALOG_MESSAGE,
                    add_reject_option=True,
                    reject_text="Cancel Upload",
                    accept_text="Upload Anyway",
                    alternative_accept_text="Upload Anyway",
                    level=QtWidgets.QMessageBox.Warning,
                )

                if reply == QMessageBox.RejectRole:
                    raise Exception("Upload cancelled")

                continue  # TODO: IDEA IMPLEMENT POP UP CONFIRMATION OF DELETE FEATURE WHEN MISSING GEOMETRIES.

            media_key = None

            if "media_key" in feature_attributes:
                media_key = parse_field(feature_attributes, field_name="media_key")

            if location_geometry is None:
                logger.error(f"{location_geometry=}")

            if location_geometry is not None:
                common_kvs = dict(
                    admin_id=admin_id,
                    external_id=external_id,
                    floor_key=floor_key,
                    is_active=is_active,
                    is_searchable=is_searchable,
                    location_type_key=location_type_key,
                    translations=(translations),
                    display_rule=extract_display_rule(feature_attributes),
                    media_key=media_key,
                    restrictions=restrictions,
                    is_selectable=is_selectable,
                    settings_3d_margin=settings_3d_margin,
                    settings_3d_width=settings_3d_width,
                    active_from=active_from,
                    active_to=active_to,
                    street_view_config=street_view_config,
                )

                anchor = location_geometry.representative_point()

                if ANCHOR_AS_INDIVIDUAL_FIELDS:
                    if "anchor_x" in feature_attributes:
                        ax = extract_field_value(feature_attributes, "anchor_x")
                        feature_attributes.pop("anchor_x")
                        ay = extract_field_value(feature_attributes, "anchor_y")
                        feature_attributes.pop("anchor_y")
                        anchor = shapely.Point([ax, ay])

                else:

                    if "anchor" in feature_attributes:
                        a = extract_field_value(feature_attributes, "anchor")
                        if a is not None and not (a.isNull() or a.isEmpty()):
                            can = qgs_geometry_to_shapely(a)
                            if can:
                                anchor = can

                        feature_attributes.pop("anchor")

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
                                        ckey=category_name
                                    )
                                    if solution.categories.get(category_key) is None:
                                        if read_bool_setting(
                                            "ALLOW_CATEGORY_TYPE_CREATION"
                                        ):  # TODO: MAKE CONFIRMATION DIALOG IF TRUE
                                            try:
                                                category_key = solution.add_category(
                                                    ckey=category_name,
                                                    translations={
                                                        "en": LanguageBundle(
                                                            name=category_name
                                                        )
                                                    },
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
                        elif k == "details":
                            details = []
                            a = extract_field_value(feature_attributes, "details")

                            if not isinstance(a, Collection):
                                logger.warning(f"Skipping {a} for {k}")
                                continue

                            for detail_entry in a:
                                if isinstance(detail_entry, str):
                                    detail_entry_key = detail_entry.lower().strip()
                                    if detail_entry_key == "":
                                        continue

                                    if False:
                                        ddd = ast.literal_eval(
                                            detail_entry
                                        )  # TODO: MAKE SAFE?
                                    else:
                                        ddd = eval(detail_entry)

                                    if "__class__.__name__" in ddd:
                                        detail_type = ddd.pop("__class__.__name__")

                                        assert isinstance(
                                            detail_type, str
                                        ), f"{type(detail_type)} is not a supported detail type, ({StrToDetailTypeMap.keys()})"
                                        detail_type = StrToDetailTypeMap[
                                            detail_type.strip()
                                        ]

                                        if detail_type == OpeningHoursDetail:
                                            opening_hours = (
                                                standard_opening_hours_from_dict(
                                                    ddd.pop("opening_hours")
                                                )
                                            )

                                            details.append(
                                                OpeningHoursDetail(
                                                    **ddd, opening_hours=opening_hours
                                                )
                                            )
                                        else:
                                            details.append(detail_type(**ddd))
                                    else:
                                        logger.error(
                                            f'Did not find a "__class__.__name__" in {ddd}, skipping it'
                                        )

                            if details:
                                common_kvs["details"] = details
                        else:
                            ...
                            # logger.debug(f'Unknown {k}')
                            # common_kvs[k] = extract_field_value(feature_attributes, k)
                    else:
                        # logger.debug("Already in kvs")
                        ...

                shapely_geom = prepare_geom_for_mi_db_qgis(location_geometry)

                try:
                    if backend_location_type == BackendLocationTypeEnum.ROOM:
                        location_key = solution.add_room(
                            polygon=shapely_geom,
                            anchor=prepare_geom_for_mi_db_qgis(anchor),
                            **common_kvs,
                        )
                    elif backend_location_type == BackendLocationTypeEnum.AREA:
                        location_key = solution.add_area(
                            polygon=shapely_geom,
                            is_obstacle=is_obstacle,
                            anchor=prepare_geom_for_mi_db_qgis(anchor),
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
            else:
                logger.error(f"{location_geometry=}")


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
