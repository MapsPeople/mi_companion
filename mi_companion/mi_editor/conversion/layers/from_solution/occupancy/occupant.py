import logging
from typing import Any, List, Optional

from jord.pandas_utilities import df_to_columns
from jord.qgis_utilities import (
    make_field_not_null,
    make_field_reuse_last_entered_value,
    make_field_unique,
)
from jord.qlive_utilities import add_no_geom_layer
from sync_module.model import Solution
from sync_module.tools import collection_to_df, process_nested_fields_df

BOOLEAN_OCCUPANT_ATTRS = ()
STR_OCCUPANT_ATTRS = ()  # ("name",)
FLOAT_OCCUPANT_ATTRS = ()
INT_OCCUPANT_ATTRS = ()

logger = logging.getLogger(__name__)

__all__ = ["add_occupant_layer"]


def add_occupant_layer(
    solution: Solution,
    *,
    qgis_instance_handle: Any,
    venue_group: Any,
) -> Optional[List[Any]]:  # QgsVectorLayer
    """

    :param solution:
    :param qgis_instance_handle:
    :param venue_group:
    :return:
    """

    # TODO: MAKE NO GEOMETRY LAYER WITH VALUE REFERENCES COLUMN TO LAYER
    # OR INVERT RELATION FROM OCCUPANT TO LOCATION, into LOCATION TO OCCUPANT LAYER

    shape_df = collection_to_df(solution.occupants)

    column_selection = [
        c
        for c in shape_df.columns
        if ("." not in c)
        or (
            "translations." in c
            and (".translations" not in c)  # Only this objects translations
        )
    ]

    if column_selection:
        selected = shape_df[column_selection]
    else:
        selected = shape_df

    selected = process_nested_fields_df(selected)

    if not len(shape_df):
        logger.warning(f"Nothing to be added, skipping occupants layer")
        return None

    for attr_name in BOOLEAN_OCCUPANT_ATTRS:
        selected[attr_name] = shape_df[attr_name].astype(bool)

    for attr_name in STR_OCCUPANT_ATTRS:
        selected[attr_name] = shape_df[attr_name].astype(str)

    for attr_name in FLOAT_OCCUPANT_ATTRS:
        selected[attr_name] = shape_df[attr_name].astype(float)

    for attr_name in INT_OCCUPANT_ATTRS:
        selected[attr_name] = shape_df[attr_name].astype(int)

    columns = df_to_columns(selected)

    added_layers = add_no_geom_layer(
        qgis_instance_handle=qgis_instance_handle,
        columns=columns,
        name="occupants",
        group=venue_group,
    )

    make_field_unique(added_layers, field_name="key")

    if False:
        for field_name in ("name",):
            make_field_not_null(added_layers, field_name=field_name)

        for field_name in ("name",):
            make_field_reuse_last_entered_value(added_layers, field_name=field_name)

    return added_layers
