import logging
from typing import Any, Iterable, List, Optional

from jord.qgis_utilities import (
    add_dropdown_widget,
    make_field_default,
    make_field_not_null,
    make_field_reuse_last_entered_value,
    make_field_unique,
)
from jord.qlive_utilities import add_no_geom_layer

from integration_system.model import CollectionMixin
from mi_companion.mi_editor import process_custom_props_df, to_df

BOOLEAN_OCCUPANT_ATTRS = ()
STR_OCCUPANT_ATTRS = ("description", "name", "admin_id")
FLOAT_OCCUPANT_ATTRS = ()
INT_OCCUPANT_ATTRS = ()

logger = logging.getLogger(__name__)

__all__ = ["add_occupant_layer"]


def add_occupant_layer(
    location_collection: CollectionMixin,
    name: str,
    *,
    qgis_instance_handle: Any,
    floor_group: Any,
    dropdown_widget: Optional[Any] = None,
    opacity: float = 1.0,
) -> Optional[List[Any]]:  # QgsVectorLayer

    # TODO: MAKE NO GEOMETRY LAYER WITH VALUE REFERENCES COLUMN TO LAYER
    # OR INVERT RELATION FROM OCCUPANT TO LOCATION, into LOCATION TO OCCUPANT LAYER

    shape_df = to_df(location_collection)

    assert len(location_collection) == len(shape_df)
    if shape_df.empty:
        logger.warning(f"{name=} {shape_df=} was empty!")

        return

    column_selection = [
        c
        for c in shape_df.columns
        if ("." not in c)
        or (
            "custom_properties." in c
            and (".custom_properties" not in c)  # Only this objects custom_properties
        )
    ]

    if column_selection:
        selected = shape_df[column_selection]
    else:
        selected = shape_df

    process_custom_props_df(selected)

    if not len(shape_df):
        # logger.warning(f"Nothing to be added, skipping {name}")
        return

    for attr_name in BOOLEAN_OCCUPANT_ATTRS:
        selected[attr_name] = shape_df[attr_name].astype(bool)

    for attr_name in STR_OCCUPANT_ATTRS:
        selected[attr_name] = shape_df[attr_name].astype(str)

    for attr_name in FLOAT_OCCUPANT_ATTRS:
        selected[attr_name] = shape_df[attr_name].astype(float)

    for attr_name in INT_OCCUPANT_ATTRS:
        selected[attr_name] = shape_df[attr_name].astype(int)

    added_layers = add_no_geom_layer(
        qgis_instance_handle=qgis_instance_handle,
        dataframe=selected,
        name=name,
        group=floor_group,
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

    if dropdown_widget:
        add_dropdown_widget(
            added_layers,
            "location_type.name",
            dropdown_widget,
        )

    make_field_unique(added_layers, field_name="admin_id")

    for field_name in ("name", "location_type.name", "is_searchable", "is_active"):
        make_field_not_null(added_layers, field_name=field_name)

    for field_name, field_default in {"is_searchable": True, "is_active": True}.items():
        make_field_default(
            added_layers, field_name=field_name, default_expression=f"'{field_default}'"
        )

    for field_name in ("name", "location_type.name", "is_searchable", "is_active"):
        make_field_reuse_last_entered_value(added_layers, field_name=field_name)

    return added_layers
