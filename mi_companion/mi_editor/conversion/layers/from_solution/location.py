import logging
from typing import Any, Iterable, List, Optional

import geopandas
import pandas

# noinspection PyUnresolvedReferences
import qgis

# noinspection PyUnresolvedReferences
from qgis.core import QgsEditorWidgetSetup

from jord.qgis_utilities import (
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
from jord.qgis_utilities.helpers.widgets import COLOR_WIDGET
from jord.qlive_utilities import add_dataframe_layer
from mi_companion import ANCHOR_AS_INDIVIDUAL_FIELDS
from mi_companion.configuration import read_bool_setting, read_float_setting
from mi_companion.constants import (
    FLOOR_HEIGHT,
    FLOOR_VERTICAL_SPACING,
    USE_EXTERNAL_ID_FLOOR_SELECTION,
)
from mi_companion.mi_editor.conversion.layers.from_solution.location_fields import (
    BOOLEAN_LOCATION_FIELDS,
    COLOR_LOCATION_FIELDS,
    DATETIME_LOCATION_FIELDS,
    FLOAT_LOCATION_FIELDS,
    INT_LOCATION_FIELDS,
    LocationGeometryType,
    NOT_NULL_FIELDS,
    RANGE_LOCATION_FIELDS,
    REUSE_LAST_FIELDS,
    STR_LOCATION_FIELDS,
)
from mi_companion.mi_editor.conversion.projection import (
    forward_project_qgis,
    reproject_geometry_df_qgis,
    should_reproject_qgis,
    solve_target_crs_authid,
)
from mi_companion.mi_editor.conversion.styling import (
    add_raster_symbol,
    add_rotation_scale_geometry_generator,
    add_svg_symbol,
    apply_display_rule_styling_categorized,
)
from mi_companion.qgis_utilities import auto_center_anchors_when_outside
from mi_companion.type_enums import BackendLocationTypeEnum
from sync_module.model import (
    Floor,
    Solution,
)
from sync_module.model.solution_item import CollectionMixin
from sync_module.shared.pandas_utilities import locations_to_df
from sync_module.tools.serialisation import (
    collection_to_df,
)
from sync_module.tools.serialisation.parsing import process_nested_fields_df

try:
    from enum import StrEnum
except ImportError:
    from strenum import StrEnum

__all__ = ["add_floor_content_layers"]

logger = logging.getLogger(__name__)


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
            ("translations." in c or "display_rule." in c or "street_view_config." in c)
            and (
                (".translations" not in c)
                and (".display_rule" not in c)
                and (".street_view_config" not in c)
            )
            # Only this objects translations
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

    locations_df = process_nested_fields_df(locations_df)
    assert len(shape_df) == len(
        locations_df
    ), f"Some Features where dropped, should not happen! {len(shape_df)}!={len(locations_df)}"

    try:
        locations_df = locations_df[~locations_df.is_empty]
    except Exception as e:
        logger.error(f"{e}")

    reproject_geometry_df_qgis(locations_df)

    if "anchor" in locations_df:
        if should_reproject_qgis():
            locations_df["anchor"] = locations_df["anchor"].apply(forward_project_qgis)

        if ANCHOR_AS_INDIVIDUAL_FIELDS:
            locations_df["anchor_x"] = locations_df["anchor"].apply(lambda p: p.x)
            locations_df["anchor_y"] = locations_df["anchor"].apply(lambda p: p.y)
            locations_df.pop("anchor")

    assert len(shape_df) == len(
        locations_df
    ), f"Some Features where dropped, should not happen! {len(shape_df)}!={len(locations_df)}"

    if not len(shape_df):
        # logger.warning(f"Nothing to be added, skipping {name}")
        return

    if False:
        for attr_name in BOOLEAN_LOCATION_FIELDS:
            if attr_name in locations_df:
                locations_df[attr_name] = shape_df[attr_name].astype(
                    bool, errors="ignore"
                )

    for attr_name in STR_LOCATION_FIELDS:
        if attr_name in locations_df:
            locations_df[attr_name] = shape_df[attr_name].astype(str, errors="ignore")

    for attr_name in FLOAT_LOCATION_FIELDS:
        if attr_name in locations_df:
            locations_df[attr_name] = shape_df[attr_name].astype(float, errors="ignore")

    for attr_name in INT_LOCATION_FIELDS:
        if attr_name in locations_df:
            locations_df[attr_name] = shape_df[attr_name].astype(int, errors="ignore")

    for attr_name in DATETIME_LOCATION_FIELDS:
        if attr_name in locations_df:
            # locations_df[attr_name] = shape_df[attr_name].astype(datetime)
            locations_df[attr_name] = pandas.to_datetime(locations_df[attr_name])

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

    # locations_df.replace({numpy.nan: None}, inplace=True)

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

    auto_center_anchors_when_outside(added_layers)

    for field_name in NOT_NULL_FIELDS:
        make_field_not_null(added_layers, field_name=field_name)

    for field_name, field_default in {"is_searchable": True, "is_active": True}.items():
        make_field_default(
            added_layers, field_name=field_name, default_expression=f"'{field_default}'"
        )
        make_field_boolean(added_layers, field_name=field_name, nullable=False)

    if False:
        for field_name in BOOLEAN_LOCATION_FIELDS:
            make_field_boolean(added_layers, field_name=field_name)

    if False:
        if location_type_ref_layer:
            apply_display_rule_styling_categorized(layer, location_type_ref_layer)

    for field_name, field_widget in RANGE_LOCATION_FIELDS.items():
        set_field_widget(added_layers, field_name, field_widget)

    for field_name in COLOR_LOCATION_FIELDS:
        set_field_widget(added_layers, field_name, COLOR_WIDGET)

    for field_name in REUSE_LAST_FIELDS:
        make_field_reuse_last_entered_value(added_layers, field_name=field_name)

    for field_name in ("is_selectable", "is_obstacle"):
        make_field_boolean(added_layers, field_name=field_name, nullable=True)
        make_field_default(
            added_layers, field_name=field_name, default_expression=f"null"
        )

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

    add_raster_symbol(room_layers)
    add_svg_symbol(room_layers)
    add_rotation_scale_geometry_generator(room_layers)

    if read_bool_setting("USE_LOCATION_TYPE_FOR_LABEL"):  # TODO: STILL DOES NOT WORK...
        label_field_name = 'represent_value("location_type")'
    else:
        label_field_name = "name"

    set_label_styling(
        room_layers,
        field_name=label_field_name,
        min_ratio=read_float_setting("LAYER_LABEL_VISIBLE_MIN_RATIO"),
    )

    set_layer_rendering_scale(
        room_layers,
        min_ratio=read_float_setting("LAYER_GEOM_VISIBLE_MIN_RATIO"),
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
        min_ratio=read_float_setting("LAYER_LABEL_VISIBLE_MIN_RATIO"),
    )

    set_layer_rendering_scale(
        area_layers,
        min_ratio=read_float_setting("LAYER_GEOM_VISIBLE_MIN_RATIO"),
    )

    add_raster_symbol(area_layers)
    add_svg_symbol(area_layers)
    add_rotation_scale_geometry_generator(area_layers)

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
        poi_layers,
        field_name=label_field_name,
        min_ratio=read_float_setting("LAYER_LABEL_VISIBLE_MIN_RATIO"),
    )

    set_layer_rendering_scale(
        poi_layers,
        min_ratio=read_float_setting("LAYER_GEOM_VISIBLE_MIN_RATIO"),
    )

    add_raster_symbol(poi_layers)
    add_svg_symbol(poi_layers)  # NO ANCHOR HERE..

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
