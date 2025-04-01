import logging
from typing import Any, List, Optional

from integration_system.model import Solution
from integration_system.pandas_serde import collection_to_df
from jord.pandas_utilities import df_to_columns
from jord.qgis_utilities import (
    make_field_not_null,
    make_field_unique,
)
from jord.qlive_utilities import add_no_geom_layer
from .custom_props import process_custom_props_df

BOOLEAN_LOCATION_TYPE_ATTRS = ()
STR_LOCATION_TYPE_ATTRS = ("name", "admin_id")
FLOAT_LOCATION_TYPE_ATTRS = ()
INTEGER_LOCATION_TYPE_ATTRS = ()

logger = logging.getLogger(__name__)

__all__ = ["add_location_type_layer"]


def set_display_rule_conditional_formatting(): ...


def add_location_type_layer(
    solution: Solution,
    *,
    layer_name: str,
    qgis_instance_handle: Any,
    solution_group: Any
) -> Optional[List[Any]]:  # QgsVectorLayer

    shape_df = collection_to_df(solution.location_types)

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
        return None

    for attr_name in BOOLEAN_LOCATION_TYPE_ATTRS:
        selected[attr_name] = shape_df[attr_name].astype(bool)

    for attr_name in STR_LOCATION_TYPE_ATTRS:
        selected[attr_name] = shape_df[attr_name].astype(str)

    for attr_name in FLOAT_LOCATION_TYPE_ATTRS:
        selected[attr_name] = shape_df[attr_name].astype(float)

    for attr_name in INTEGER_LOCATION_TYPE_ATTRS:
        selected[attr_name] = shape_df[attr_name].astype(int)

    columns = df_to_columns(shape_df, ["key"])

    added_layers = add_no_geom_layer(
        qgis_instance_handle=qgis_instance_handle,
        name=layer_name,
        group=solution_group,
        columns=columns,
        visible=True,
    )

    make_field_unique(added_layers, field_name="admin_id")

    for field_name in ("name",):
        make_field_not_null(added_layers, field_name=field_name)

    return added_layers
