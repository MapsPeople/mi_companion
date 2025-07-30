import logging
from typing import Any, Iterable, Optional, Tuple

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets

# noinspection PyUnresolvedReferences
from qgis.core import QgsEditorWidgetSetup, QgsProject

from jord.qgis_utilities import (
    make_enum_dropdown_widget,
    make_iterable_dropdown_widget,
    make_sorted_mapping_dropdown_widget,
    make_value_map_widget,
)
from jord.qlive_utilities import add_no_geom_layer
from mi_companion import (
    ADD_LOCATION_TYPE_LAYERS,
    DESCRIPTOR_BEFORE,
    OSM_HIGHWAY_TYPES,
)
from mi_companion.configuration import read_bool_setting
from mi_companion.layer_descriptors import (
    DATABASE_GROUP_DESCRIPTOR,
    LOCATION_TYPE_DESCRIPTOR,
    SOLUTION_DATA_DESCRIPTOR,
    SOLUTION_GROUP_DESCRIPTOR,
)
from sync_module.mi import (
    SolutionDepth,
    get_remote_solution,
)
from sync_module.model import (
    GraphEdgeContextTypes,
    IMPLEMENTATION_STATUS,
    Solution,
)
from sync_module.shared import (
    MIConnectionType,
    MIDoorType,
    MIEntryPointType,
    MIVenueType,
)
from .location_type import add_location_type_layer, make_location_type_dropdown_widget
from .venue import add_venue_layer

__all__ = ["solution_venue_to_layer_hierarchy", "add_solution_layers"]

logger = logging.getLogger(__name__)


def add_solution_layers(
    *,
    qgis_instance_handle: Any,
    solution: Solution,
    layer_tree_root: Any,
    mi_hierarchy_group_name: str = DATABASE_GROUP_DESCRIPTOR,
    progress_bar: Optional[QtWidgets.QProgressBar] = None,
) -> None:
    """

    :param qgis_instance_handle:
    :param solution:
    :param layer_tree_root:
    :param mi_hierarchy_group_name:
    :param progress_bar:
    :return:
    """
    (
        available_location_type_dropdown_widget,
        connection_type_dropdown_widget,
        door_type_dropdown_widget,
        edge_context_type_dropdown_widget,
        entry_point_type_dropdown_widget,
        highway_type_dropdown_widget,
        solution_group,
        venue_type_dropdown_widget,
        location_type_ref_layer,
    ) = add_solution_group(
        layer_tree_root,
        mi_hierarchy_group_name,
        progress_bar,
        qgis_instance_handle,
        solution,
    )

    add_venue_layer(
        progress_bar=progress_bar,
        qgis_instance_handle=qgis_instance_handle,
        solution=solution,
        solution_group=solution_group,
        location_type_ref_layer=location_type_ref_layer,
        location_type_dropdown_widget=available_location_type_dropdown_widget,
        door_type_dropdown_widget=door_type_dropdown_widget,
        highway_type_dropdown_widget=highway_type_dropdown_widget,
        venue_type_dropdown_widget=venue_type_dropdown_widget,
        connection_type_dropdown_widget=connection_type_dropdown_widget,
        entry_point_type_dropdown_widget=entry_point_type_dropdown_widget,
        edge_context_type_dropdown_widget=edge_context_type_dropdown_widget,
    )


def add_solution_group(
    layer_tree_root: Any,
    mi_hierarchy_group_name: str,
    progress_bar: callable,
    qgis_instance_handle: Any,
    solution: Solution,
) -> Tuple:
    """

    :param layer_tree_root:
    :param mi_hierarchy_group_name:
    :param progress_bar:
    :param qgis_instance_handle:
    :param solution:
    :return:
    """

    mi_group = layer_tree_root.findGroup(mi_hierarchy_group_name)
    if not mi_group:  # add it if it does not exist
        mi_group = layer_tree_root.addGroup(mi_hierarchy_group_name)

    mi_group.setExpanded(True)
    # mi_group.setExpanded(False)
    if DESCRIPTOR_BEFORE:
        solution_name = f"{SOLUTION_GROUP_DESCRIPTOR} {solution.name}"
    else:
        solution_name = f"{solution.name} {SOLUTION_GROUP_DESCRIPTOR}"

    solution_group = layer_tree_root.findGroup(solution_name)

    if not solution_group:
        solution_group = mi_group.insertGroup(0, solution_name)

    solution_group.setExpanded(True)
    # solution_group.setExpanded(False)

    door_type_dropdown_widget = None
    if read_bool_setting("MAKE_DOOR_TYPE_DROPDOWN"):
        door_type_dropdown_widget = make_enum_dropdown_widget(MIDoorType)

    highway_type_dropdown_widget = None
    if read_bool_setting("MAKE_HIGHWAY_TYPE_DROPDOWN"):
        highway_type_dropdown_widget = make_sorted_mapping_dropdown_widget(
            OSM_HIGHWAY_TYPES
        )

    venue_type_dropdown_widget = None
    if read_bool_setting("MAKE_VENUE_TYPE_DROPDOWN"):
        venue_type_dropdown_widget = make_enum_dropdown_widget(MIVenueType)

    entry_point_type_dropdown_widget = None
    if read_bool_setting("MAKE_ENTRY_POINT_TYPE_DROPDOWN"):
        entry_point_type_dropdown_widget = make_enum_dropdown_widget(MIEntryPointType)

    connection_type_dropdown_widget = None
    if read_bool_setting("MAKE_CONNECTION_TYPE_DROPDOWN"):
        connection_type_dropdown_widget = make_enum_dropdown_widget(MIConnectionType)

    edge_context_type_dropdown_widget = None
    if read_bool_setting("MAKE_EDGE_CONTEXT_TYPE_DROPDOWN"):
        edge_context_type_dropdown_widget = make_iterable_dropdown_widget(
            GraphEdgeContextTypes
        )

    # solution_layer_name = f"{solution.name}_solution_data"
    # solution_data_layers = QgsProject.instance().mapLayersByName(solution_layer_name)
    # logger.info(f"Found {solution_data_layers}")
    found_solution_data = None
    # found_solution_data = len(solution_data_layers)>0
    for c in solution_group.children():
        if SOLUTION_DATA_DESCRIPTOR in c.name():
            found_solution_data = c

    if found_solution_data is not None:
        reply = QtWidgets.QMessageBox.question(
            None,
            f"Solution Data layer for ({found_solution_data.name()}) was already found",
            f"Solution data ({found_solution_data.name()}) will be reloaded with the most recent data from th MapsIndoors database!\n"
            f"Accept?",
        )

        if reply == QtWidgets.QMessageBox.Yes:
            solution_group.removeChildNode(found_solution_data)
            found_solution_data = None
        else:
            ...

    if found_solution_data is None:
        solution_data_layers = add_no_geom_layer(
            qgis_instance_handle=qgis_instance_handle,
            name=SOLUTION_DATA_DESCRIPTOR,
            group=solution_group,
            columns=[
                {
                    "external_id": solution.external_id,
                    "name": solution.name,
                    "customer_id": solution.customer_id,
                    "occupants_enabled": solution.occupants_enabled,
                    "available_languages": solution.available_languages,
                    "implementation_type": str(solution.implementation_type),
                    "default_language": solution.default_language,
                }
            ],
            visible=False,
        )

        implementation_type_dropdown_widget = make_sorted_mapping_dropdown_widget(
            IMPLEMENTATION_STATUS
        )

        for layers_inner in solution_data_layers:
            if layers_inner:
                if isinstance(layers_inner, Iterable):
                    for solution_data_layer in layers_inner:
                        if solution_data_layer:
                            solution_data_layer.setEditorWidgetSetup(
                                solution_data_layers.fields().indexFromName(
                                    "implementation_type"
                                ),
                                implementation_type_dropdown_widget,
                            )
                else:
                    layers_inner.setEditorWidgetSetup(
                        layers_inner.fields().indexFromName("implementation_type"),
                        implementation_type_dropdown_widget,
                    )

    if False:
        default_language_dropdown_widget = None
        if read_bool_setting("MAKE_ENTRY_POINT_TYPE_DROPDOWN"):
            default_language_dropdown_widget = make_enum_dropdown_widget(
                MIEntryPointType
            )

    if progress_bar:
        progress_bar.setValue(10)

    available_location_type_dropdown_widget = None
    location_type_ref_layer = None

    if False:  # TODO: RELOAD LOCATION_TYPE LAYER AND REFERENCES
        for c in solution_group.children():
            if LOCATION_TYPE_DESCRIPTOR in c.name():
                found_location_type_data = c

        if found_location_type_data is not None:
            reply = QtWidgets.QMessageBox.question(
                None,
                f"LocationType data ({found_solution_data.name()}) will be reloaded with the newest data!",
                f"Accept?",
            )

    if ADD_LOCATION_TYPE_LAYERS:
        location_type_layer = None

        for c in solution_group.children():
            if LOCATION_TYPE_DESCRIPTOR in c.name():
                reply = QtWidgets.QMessageBox.question(
                    None,
                    f"Location Type layer for ({c.name()}) was already found",
                    f"Location Type ({c.name()}) will be reloaded with the most recent data from th MapsIndoors database!\n"
                    f"Accept?",
                )

                if reply == QtWidgets.QMessageBox.Yes:
                    solution_group.removeChildNode(c)
                    location_type_layer = None
                else:
                    ...

        for c in solution_group.children():
            if LOCATION_TYPE_DESCRIPTOR in c.name():
                location_type_layer = [c.layer()]
                logger.info(f"Found location type layer: {LOCATION_TYPE_DESCRIPTOR}")
                break

        if (
            location_type_layer is None
        ):  # TODO: RELOAD LOCATION_TYPE LAYER AND REFERENCES
            location_type_layer = add_location_type_layer(
                solution,
                qgis_instance_handle=qgis_instance_handle,
                solution_group=solution_group,
                layer_name=LOCATION_TYPE_DESCRIPTOR,
            )
            logger.info(f"Adding location type layer: {LOCATION_TYPE_DESCRIPTOR}")

        if len(location_type_layer):
            location_type_layer = location_type_layer[0]

            available_location_type_dropdown_widget = make_location_type_dropdown_widget(
                location_type_layer.id(),
                target_key_field_name="admin_id",
                target_value_field_name=f"translations.{solution.default_language}.name",
            )
            location_type_ref_layer = location_type_layer

    else:
        if read_bool_setting("MAKE_LOCATION_TYPE_DROPDOWN"):
            available_location_type_dropdown_widget = make_value_map_widget(
                {
                    solution.location_types.get(k)
                    .translations[solution.default_language]
                    .name: solution.location_types.get(k)
                    .translations[solution.default_language]
                    .name
                    for k in sorted(solution.location_types.keys)
                }
            )

    return (
        available_location_type_dropdown_widget,
        connection_type_dropdown_widget,
        door_type_dropdown_widget,
        edge_context_type_dropdown_widget,
        entry_point_type_dropdown_widget,
        highway_type_dropdown_widget,
        solution_group,
        venue_type_dropdown_widget,
        location_type_ref_layer,
    )


def solution_venue_to_layer_hierarchy(
    qgis_instance_handle: Any,
    solution_external_id: str,
    venue_external_id: str,
    mi_hierarchy_group_name: str = DATABASE_GROUP_DESCRIPTOR,
    *,
    progress_bar: Optional[QtWidgets.QProgressBar] = None,
    include_occupants: bool = True,
    include_media: bool = False,
    include_route_elements: bool = True,
    include_graph: bool = True,
    depth: SolutionDepth = SolutionDepth.occupants,
) -> Solution:
    """
    Return solution and created widget objects


    :param include_occupants:
    :param include_media:
    :param include_route_elements:
    :param include_graph:
    :param depth:
    :param qgis_instance_handle:
    :param solution_external_id:
    :param venue_external_id:
    :param mi_hierarchy_group_name:
    :param settings:
    :param progress_bar:
    :return:
    """
    if progress_bar:
        progress_bar.setValue(0)

    layer_tree_root = QgsProject.instance().layerTreeRoot()

    solution = get_remote_solution(
        solution_external_id,
        venue_keys=[venue_external_id],
        include_occupants=include_occupants,
        include_media=include_media,
        include_route_elements=include_route_elements,
        include_graph=include_graph,
        depth=depth,
    )

    add_solution_layers(
        qgis_instance_handle=qgis_instance_handle,
        solution=solution,
        layer_tree_root=layer_tree_root,
        mi_hierarchy_group_name=mi_hierarchy_group_name,
        progress_bar=progress_bar,
    )

    return solution
