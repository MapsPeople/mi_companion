import copy
import dataclasses
import json
import logging
from typing import Any, Collection, Iterable, List, Optional

import geopandas

# noinspection PyUnresolvedReferences
import qgis
from pandas import DataFrame, json_normalize

# noinspection PyUnresolvedReferences
from qgis.core import QgsEditorWidgetSetup

from integration_system.model import (
    CollectionMixin,
    DisplayRule,
    Floor,
    Media,
    Solution,
)
from integration_system.tools.serialisation import (
    collection_to_df,
)
from integration_system.tools.serialisation import to_dict_with_dataclass_type
from jord.qgis_utilities import (
    HIDDEN_WIDGET,
    make_field_boolean,
    make_field_default,
    make_field_not_null,
    make_field_reuse_last_entered_value,
    make_field_unique,
    set_3d_view_settings,
    set_field_widget,
    set_geometry_constraints,
    set_label_styling,
    set_layer_rendering_scale,
    styled_field_value_categorised,
)
from jord.qlive_utilities import add_dataframe_layer
from mi_companion import (
    LAYER_GEOM_VISIBLE_MIN_RATIO,
    LAYER_LABEL_VISIBLE_MIN_RATIO,
    REAL_NONE_JSON_VALUE,
)
from mi_companion.configuration.options import read_bool_setting
from mi_companion.constants import (
    FLOOR_HEIGHT,
    FLOOR_VERTICAL_SPACING,
    USE_EXTERNAL_ID_FLOOR_SELECTION,
)
from .parsing import process_nested_fields_df
from ..type_enums import BackendLocationTypeEnum
from ...projection import (
    reproject_geometry_df,
    solve_target_crs_authid,
)

try:
    from enum import StrEnum
except ImportError:
    from strenum import StrEnum

__all__ = ["add_floor_content_layers", "locations_to_df", "LocationGeometryType"]

logger = logging.getLogger(__name__)

BOOLEAN_LOCATION_ATTRS = ("is_searchable", "is_active")
STR_LOCATION_ATTRS = ("description", "external_id", "name", "admin_id")
FLOAT_LOCATION_ATTRS = ()
INT_LOCATION_ATTRS = ()

# FIELDS_HIDDEN_IN_FORM = ('is_searchable', 'is_active', 'admin_id')
FORM_FIELDS = ("name", "location_type")


class LocationGeometryType(StrEnum):
    point = "point"
    # linestring = "linestring"
    polygon = "polygon"


def locations_to_df(collection_: CollectionMixin) -> DataFrame:
    """

    :param collection_:
    :return:
    """

    # noinspection PyTypeChecker
    converted_items = []

    for item in collection_:
        if False:
            if hasattr(item, "custom_properties"):
                custom_properties = getattr(item, "custom_properties")
                if custom_properties is not None:
                    for language, translations in copy.deepcopy(
                        custom_properties
                    ).items():
                        for custom_property, value in translations.items():
                            if value is None:
                                custom_properties[language][
                                    custom_property
                                ] = REAL_NONE_JSON_VALUE

                    setattr(item, "custom_properties", custom_properties)

        item_as_dict = dataclasses.asdict(
            item, dict_factory=to_dict_with_dataclass_type
        )

        if "details" in item_as_dict:
            list_of_details = item_as_dict.pop("details")

            deets = []
            if list_of_details:
                for d in list_of_details:
                    deets.append(repr(d))

            item_as_dict["details"] = deets

        if "display_rule" in item_as_dict:
            display_rule: DisplayRule = item_as_dict.pop("display_rule")
            if display_rule is not None:
                item_as_dict["display_rule"] = display_rule.model_dump()

        if "media" in item_as_dict:
            media = item_as_dict.pop("media")
            if media is not None:
                if isinstance(media, Media):
                    item_as_dict["media_key"] = media.key
                else:
                    assert isinstance(media, str)
                    item_as_dict["media_key"] = media

        if "categories" in item_as_dict:
            list_of_category_dicts = item_as_dict.pop("categories")

            keys = []
            if list_of_category_dicts:
                for cat in list_of_category_dicts:
                    if False:
                        a = json.loads(cat["name"])
                        if isinstance(a, str):
                            keys.append(a)
                        elif isinstance(a, Collection):
                            keys.extend(a)
                        else:
                            raise NotImplementedError(f"{type(a)} is not supported")
                    else:
                        keys.append(cat["name"])

            item_as_dict["category_keys"] = keys

        item_as_dict["key"] = item.key

        if "type" in item_as_dict:
            item_as_dict.pop("type")

        converted_items.append(item_as_dict)

    # logger.warning(f"converted {(converted_items)} items")

    a = json_normalize(converted_items)

    # logger.warning(f"normalized {(a)} items")

    if not a.empty:
        a.set_index("key", inplace=True)

    return a


def add_location_layer(
    location_collection: CollectionMixin,
    name: str,
    geometry_column_name: LocationGeometryType,
    *,
    occupant_collection: Optional[CollectionMixin] = None,
    qgis_instance_handle: Any,
    floor_group: Any,
    floor: Floor,
    location_type_ref_layer: Optional[Any] = None,
    location_type_dropdown_widget: Optional[Any] = None,
    occupant_dropdown_widget: Optional[Any] = None,
    opacity: float = 1.0,
) -> Optional[List[Any]]:  # QgsVectorLayer
    """

    :param location_type_ref_layer:
    :param location_collection:
    :param name:
    :param geometry_column_name:
    :param occupant_collection:
    :param qgis_instance_handle:
    :param floor_group:
    :param floor:
    :param location_type_dropdown_widget:
    :param occupant_dropdown_widget:
    :param opacity:
    :return:
    """

    shape_df = locations_to_df(location_collection)

    assert len(location_collection) == len(shape_df)
    if shape_df.empty:
        logger.info(f"{name=} {shape_df=} was empty!")

        return

    # logger.info(f"adding {name=} with {len(collection_)} elements")

    if USE_EXTERNAL_ID_FLOOR_SELECTION:  # OLD WAY
        floor_selection = shape_df["floor.external_id"] == floor.external_id
    else:
        floor_selection = (shape_df["floor.floor_index"] == floor.floor_index) & (
            shape_df["floor.building.admin_id"] == floor.building.admin_id
        )  # TODO: USE Floor.compute_key instead

    shape_df = shape_df[floor_selection]

    if len(shape_df) == 0:
        # logger.warning(f"No location were found for {floor.__desc__}")

        return

    # logger.warning(shape_df.columns)

    column_selection = [
        c
        for c in shape_df.columns
        if ("." not in c)
        or ("location_type.admin_id" == c)
        or (
            ("custom_properties." in c or "display_rule." in c)
            and ((".custom_properties" not in c) and (".display_rule" not in c))
            # Only this objects custom_properties
        )
    ]

    if column_selection:
        selected = shape_df[column_selection]
    else:
        selected = shape_df

    locations_df = geopandas.GeoDataFrame(selected, geometry=geometry_column_name.value)
    assert len(shape_df) == len(
        locations_df
    ), f"Some Features where dropped, should not happen! {len(shape_df)}!={len(locations_df)}"

    process_nested_fields_df(locations_df)
    assert len(shape_df) == len(
        locations_df
    ), f"Some Features where dropped, should not happen! {len(shape_df)}!={len(locations_df)}"

    empty_lines = locations_df[locations_df.is_empty]
    if not empty_lines.empty:
        logger.warning(f"Dropping {empty_lines}")

    locations_df = locations_df[~locations_df.is_empty]

    reproject_geometry_df(locations_df)
    assert len(shape_df) == len(
        locations_df
    ), f"Some Features where dropped, should not happen! {len(shape_df)}!={len(locations_df)}"

    if not len(shape_df):
        # logger.warning(f"Nothing to be added, skipping {name}")
        return

    for attr_name in BOOLEAN_LOCATION_ATTRS:
        locations_df[attr_name] = shape_df[attr_name].astype(bool)

    for attr_name in STR_LOCATION_ATTRS:
        locations_df[attr_name] = shape_df[attr_name].astype(str)

    for attr_name in FLOAT_LOCATION_ATTRS:
        locations_df[attr_name] = shape_df[attr_name].astype(float)

    for attr_name in INT_LOCATION_ATTRS:
        locations_df[attr_name] = shape_df[attr_name].astype(int)

    locations_df.rename(
        columns={"location_type.admin_id": "location_type"}, inplace=True
    )

    if occupant_dropdown_widget:
        if occupant_collection:
            a = collection_to_df(occupant_collection)
            locations_df["occupant"] = locations_df.index.map(
                lambda x: x if x in a.index else None
            )
        else:
            locations_df["occupant"] = locations_df.index

    added_layers = add_dataframe_layer(
        qgis_instance_handle=qgis_instance_handle,
        dataframe=locations_df,
        geometry_column=geometry_column_name.value,
        name=name,
        group=floor_group,
        # categorise_by_attribute="location_type",
        crs=solve_target_crs_authid(),
        opacity=opacity,
    )

    layer = None
    for a in added_layers:
        if a:
            if isinstance(a, Iterable):
                for i in a:
                    if i:
                        layer = i
                        break
                if layer:
                    break
            else:
                layer = a
                break
    else:
        # logger.warning(            f"Did not add any {geom_type} layers for {name}:{floor.__desc__}!"        )
        return

    assert (
        len(shape_df) == layer.featureCount()
    ), f"Some Features where dropped, should not happen! {len(shape_df)}!={layer.featureCount()}"

    if location_type_dropdown_widget:
        set_field_widget(
            added_layers,
            "location_type",
            location_type_dropdown_widget,
        )

    for a in added_layers:
        styled_field_value_categorised(
            a, style_attributes_layer=location_type_ref_layer
        )

    if occupant_dropdown_widget:
        set_field_widget(
            added_layers,
            "occupant",
            occupant_dropdown_widget,
        )

    make_field_unique(added_layers, field_name="admin_id")

    for field_name in ("name", "location_type", "is_searchable", "is_active"):
        make_field_not_null(added_layers, field_name=field_name)

    for field_name, field_default in {"is_searchable": True, "is_active": True}.items():
        make_field_default(
            added_layers, field_name=field_name, default_expression=f"'{field_default}'"
        )

    if False:
        for qgs_field_name in layer.fields():
            field_name = qgs_field_name.name()
            hide = True
            for visible_form_field_name in FORM_FIELDS:
                if visible_form_field_name in field_name:
                    hide = False

            if hide:
                set_field_widget(added_layers, field_name, HIDDEN_WIDGET)

    if False:
        for field_name in BOOLEAN_LOCATION_ATTRS:
            make_field_boolean(added_layers, field_name=field_name)

    for field_name in ("name", "location_type", "is_searchable", "is_active"):
        make_field_reuse_last_entered_value(added_layers, field_name=field_name)

    return added_layers


def add_floor_content_layers(
    *,
    qgis_instance_handle: Any,
    solution: Solution,
    floor: Floor,
    floor_group: Any,
    location_type_ref_layer: Optional[Any] = None,
    location_type_dropdown_widget: Optional[Any] = None,
    occupant_dropdown_widget: Optional[Any] = None,
) -> None:
    """

    :param location_type_ref_layer:
    :param qgis_instance_handle:
    :param solution:
    :param floor:
    :param floor_group:
    :param location_type_dropdown_widget:
    :param occupant_dropdown_widget:
    :return:
    """
    room_layers = add_location_layer(
        location_collection=solution.rooms,
        occupant_collection=solution.occupants,
        name=BackendLocationTypeEnum.ROOM.value,
        geometry_column_name=LocationGeometryType.polygon,
        qgis_instance_handle=qgis_instance_handle,
        floor_group=floor_group,
        floor=floor,
        location_type_ref_layer=location_type_ref_layer,
        location_type_dropdown_widget=location_type_dropdown_widget,
        occupant_dropdown_widget=occupant_dropdown_widget,
        opacity=0.8,
    )

    set_3d_view_settings(
        room_layers,
        offset=FLOOR_VERTICAL_SPACING
        + (FLOOR_HEIGHT + FLOOR_VERTICAL_SPACING) * floor.floor_index,
        extrusion=FLOOR_HEIGHT,
    )

    if read_bool_setting("USE_LOCATION_TYPE_FOR_LABEL"):  # TODO: STILL DOES NOT WORK...
        label_field_name = 'represent_value("location_type")'
    else:
        label_field_name = "name"

    set_label_styling(
        room_layers,
        field_name=label_field_name,
        min_ratio=LAYER_LABEL_VISIBLE_MIN_RATIO,
    )

    if LAYER_GEOM_VISIBLE_MIN_RATIO:
        set_layer_rendering_scale(
            room_layers,
            min_ratio=LAYER_GEOM_VISIBLE_MIN_RATIO,
        )

    set_geometry_constraints(room_layers)

    area_layers = add_location_layer(
        location_collection=solution.areas,
        occupant_collection=solution.occupants,
        name=BackendLocationTypeEnum.AREA.value,
        geometry_column_name=LocationGeometryType.polygon,
        qgis_instance_handle=qgis_instance_handle,
        floor_group=floor_group,
        floor=floor,
        location_type_ref_layer=location_type_ref_layer,
        location_type_dropdown_widget=location_type_dropdown_widget,
        occupant_dropdown_widget=occupant_dropdown_widget,
        opacity=0.6,
    )
    set_label_styling(
        area_layers,
        field_name=label_field_name,
        min_ratio=LAYER_LABEL_VISIBLE_MIN_RATIO,
    )

    if LAYER_GEOM_VISIBLE_MIN_RATIO:
        set_layer_rendering_scale(
            area_layers,
            min_ratio=LAYER_GEOM_VISIBLE_MIN_RATIO,
        )

    set_geometry_constraints(area_layers)

    poi_layers = add_location_layer(
        location_collection=solution.points_of_interest,
        occupant_collection=solution.occupants,
        name=BackendLocationTypeEnum.POI.value,
        geometry_column_name=LocationGeometryType.point,
        qgis_instance_handle=qgis_instance_handle,
        floor_group=floor_group,
        floor=floor,
        location_type_ref_layer=location_type_ref_layer,
        location_type_dropdown_widget=location_type_dropdown_widget,
        occupant_dropdown_widget=occupant_dropdown_widget,
    )

    set_label_styling(
        poi_layers, field_name=label_field_name, min_ratio=LAYER_LABEL_VISIBLE_MIN_RATIO
    )

    if LAYER_GEOM_VISIBLE_MIN_RATIO:
        set_layer_rendering_scale(
            poi_layers,
            min_ratio=LAYER_GEOM_VISIBLE_MIN_RATIO,
        )

    set_geometry_constraints(poi_layers)

    if False:
        added_layers = []
        if poi_layers:
            added_layers.extend(poi_layers)
        if area_layers:
            added_layers.extend(area_layers)
        if room_layers:
            added_layers.extend(room_layers)

        for layer in added_layers:
            if False:
                # get the name of the source layer's current style
                style_name = layer.styleManager().currentStyle()

                # get the style by the name
                style = layer.styleManager().style(style_name)

                # add the style to the target layer with a custom name (in this case: 'copied')
                layer.styleManager().addStyle("copied", style)

                # set the added style as the current style
                layer.styleManager().setCurrentStyle("copied")

            layer.triggerRepaint()
            layer.emitStyleChanged()

            # src = qgis.utils.iface.setActiveLayer(layer)
            # if src:
            #  qgis.utils.iface.actionCopyLayerStyle().trigger()
            #  qgis.utils.iface.actionPasteLayerStyle().trigger()

        # actions = qgis.utils.iface.layerTreeView().defaultActions()
        # actions.showFeatureCount()  # TODO: Twice?
        # actions.showFeatureCount()
        # qgis.utils.iface.actionCopyLayerStyle().trigger()
        # qgis.utils.iface.actionPasteLayerStyle().trigger()


if __name__ == "__main__":
    print(str(LocationGeometryType.polygon))
