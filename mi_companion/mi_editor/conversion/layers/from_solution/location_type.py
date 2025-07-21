import logging

# noinspection PyUnresolvedReferences
from qgis.core import (
    QgsDefaultValue,
    QgsDefaultValue,
    QgsEditorWidgetSetup,
    QgsEditorWidgetSetup,
    QgsFieldConstraints,
    QgsFieldConstraints,
    QgsMapLayer,
)
from typing import Any, List, Optional

from integration_system.model import Solution
from integration_system.tools import collection_to_df
from jord.pandas_utilities import df_to_columns
from jord.qgis_utilities import (
    make_field_boolean,
    make_field_default,
    make_field_not_null,
    make_field_reuse_last_entered_value,
    make_field_unique,
    set_field_widget,
)
from jord.qlive_utilities import add_no_geom_layer
from .location_fields import (
    BOOLEAN_LOCATION_TYPE_ATTRS,
    FLOAT_LOCATION_TYPE_ATTRS,
    INTEGER_LOCATION_TYPE_ATTRS,
    LIST_LOCATION_TYPE_ATTRS,
    RANGE_LOCATION_ATTRS,
    STR_LOCATION_TYPE_ATTRS,
)
from .parsing import process_nested_fields_df

logger = logging.getLogger(__name__)

__all__ = ["add_location_type_layer", "make_location_type_dropdown_widget"]


def make_location_type_dropdown_widget(
    target_layer_id: str,
    *,
    target_key_field_name: str = "admin_id",
    target_value_field_name: str = "translation.en.name",
) -> Any:
    return QgsEditorWidgetSetup(
        "ValueRelation",
        {
            "AllowMulti": False,
            "AllowNull": False,
            "Description": target_key_field_name,
            "DisplayGroupName": False,
            "FilterExpression": "",
            "Group": target_value_field_name,
            "Key": target_key_field_name,
            "Layer": target_layer_id,
            "Value": target_value_field_name,
            "OrderByDescending": False,
            "OrderByField": False,
            "OrderByFieldName": "",
            "OrderByKey": False,
            "OrderByValue": True,
            "UseCompleter": False,
            "NofColumns": 1,
            "CompleterMatchFlags": 2,
        },
    )


def add_location_type_layer(
    solution: Solution,
    *,
    layer_name: str,
    qgis_instance_handle: Any,
    solution_group: Any,
) -> Optional[List[Any]]:  # QgsVectorLayer
    """

    :param solution:
    :param layer_name:
    :param qgis_instance_handle:
    :param solution_group:
    :return:
    """

    shape_df = collection_to_df(
        solution.location_types
        # , pop_keys=["display_rule"]
    )

    if False:
        column_selection = [c for c in shape_df.columns if "display_rule" not in c]
    else:
        column_selection = None

    if column_selection is not None and len(column_selection) > 0:
        selected = shape_df[column_selection]
    else:
        selected = shape_df

    process_nested_fields_df(selected)

    if not len(selected):
        # logger.warning(f"Nothing to be added, skipping {name}")
        return None

    for attr_name in BOOLEAN_LOCATION_TYPE_ATTRS:
        if attr_name in selected:
            selected[attr_name] = selected[attr_name].astype(bool, errors="ignore")

    for attr_name in STR_LOCATION_TYPE_ATTRS:
        if attr_name in selected:
            selected[attr_name] = selected[attr_name].astype(str, errors="ignore")

    for attr_name in FLOAT_LOCATION_TYPE_ATTRS:
        if attr_name in selected:
            selected[attr_name] = selected[attr_name].astype(float, errors="ignore")

    for attr_name in INTEGER_LOCATION_TYPE_ATTRS:
        if attr_name in selected:
            selected[attr_name] = selected[attr_name].astype(int, errors="ignore")

    selected.sort_values(f"translations.{solution.default_language}.name", inplace=True)

    columns = df_to_columns(selected, ["key"])

    if False:
        for r in columns:
            for attr_name in LIST_LOCATION_TYPE_ATTRS:
                if r[attr_name] is None:
                    r[attr_name] = []

    added_layers = add_no_geom_layer(
        qgis_instance_handle=qgis_instance_handle,
        name=layer_name,
        group=solution_group,
        columns=columns,
        visible=True,
    )

    make_field_unique(added_layers, field_name="admin_id")

    for field_name in ("translations.en.name",):  # TODO: ADD OTHER LANGUAGES
        make_field_not_null(added_layers, field_name=field_name)

    for field_name in ("is_selectable", "is_obstacle"):
        make_field_reuse_last_entered_value(added_layers, field_name=field_name)
        make_field_boolean(added_layers, field_name=field_name, nullable=True)
        make_field_default(
            added_layers, field_name=field_name, default_expression=f"null"
        )

    for field_name, field_widget in RANGE_LOCATION_ATTRS.items():
        set_field_widget(added_layers, field_name, field_widget)

    return added_layers
