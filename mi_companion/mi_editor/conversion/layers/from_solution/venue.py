import logging

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets
from typing import Any, Iterable, Optional

from integration_system.model import Solution, Venue
from jord.qgis_utilities import (
    make_field_not_null,
    make_field_unique,
    make_value_relation_widget,
    set_geometry_constraints,
    set_layer_rendering_scale,
)
from jord.qlive_utilities import add_shapely_layer
from mi_companion import (
    ADD_OCCUPANT_LAYERS,
    ALLOW_DUPLICATE_VENUES_IN_PROJECT,
    DESCRIPTOR_BEFORE,
)
from mi_companion.configuration import read_bool_setting, read_float_setting
from mi_companion.constants import (
    INSERT_INDEX,
)
from mi_companion.layer_descriptors import (
    VENUE_GROUP_DESCRIPTOR,
    VENUE_POLYGON_DESCRIPTOR,
)
from mi_companion.mi_editor.conversion.layers.from_solution.routing.graph import (
    add_graph_layers,
)
from mi_companion.mi_editor.conversion.projection import (
    prepare_geom_for_editing_qgis,
    solve_target_crs_authid,
)
from .building import add_building_layers
from .occupant import add_occupant_layer
from .parsing import translations_to_flattened_dict

logger = logging.getLogger(__name__)

__all__ = ["add_venue_layer"]


def add_venue_layer(
    *,
    qgis_instance_handle: Any,
    solution: Solution,
    solution_group: Any,
    location_type_ref_layer: Optional[Any] = None,
    location_type_dropdown_widget: Optional[Any] = None,
    door_type_dropdown_widget: Optional[Any] = None,
    highway_type_dropdown_widget: Optional[Any] = None,
    venue_type_dropdown_widget: Optional[Any] = None,
    connection_type_dropdown_widget: Optional[Any] = None,
    entry_point_type_dropdown_widget: Optional[Any] = None,
    edge_context_type_dropdown_widget: Optional[Any] = None,
    progress_bar: Optional[Any] = None,
) -> None:
    """

    :param location_type_ref_layer:
    :param qgis_instance_handle:
    :param solution:
    :param solution_group:
    :param location_type_dropdown_widget:
    :param door_type_dropdown_widget:
    :param highway_type_dropdown_widget:
    :param venue_type_dropdown_widget:
    :param connection_type_dropdown_widget:
    :param entry_point_type_dropdown_widget:
    :param edge_context_type_dropdown_widget:
    :param progress_bar:
    :return:
    """
    if True:
        assert len(solution.venues) > 0, "No venues found"

    for venue in solution.venues:
        if venue is None:
            logger.warning("Venue was None!")
            continue

        if DESCRIPTOR_BEFORE:
            venue_name = f"{VENUE_GROUP_DESCRIPTOR} {venue.translations[solution.default_language].name}"
        else:
            venue_name = f"{venue.translations[solution.default_language].name} {VENUE_GROUP_DESCRIPTOR}"

        venue_group = solution_group.findGroup(venue_name)
        if (
            not ALLOW_DUPLICATE_VENUES_IN_PROJECT
        ):  # TODO: base this in external ids rather than group name
            if venue_group:
                logger.error(
                    f"Venue {venue.translations[solution.default_language].name} already loaded!"
                )
                reply = QtWidgets.QMessageBox.question(
                    None,
                    f"Venue {venue.translations[solution.default_language].name} already loaded!",
                    f"Would you like to reload the {venue.translations[solution.default_language].name} venue from the MI Database?",
                )

                if reply == QtWidgets.QMessageBox.Yes:
                    solution_group.removeChildNode(venue_group)
                else:
                    continue

        venue_group = solution_group.insertGroup(
            INSERT_INDEX, venue_name
        )  # Skip solution data

        venue_group.setExpanded(True)
        venue_group.setExpanded(False)

        if INSERT_INDEX <= 0:
            add_venue_polygon_layer(
                qgis_instance_handle, venue, venue_group, venue_type_dropdown_widget
            )

        if progress_bar:
            progress_bar.setValue(20)

        occupant_dropdown_widget = None
        if ADD_OCCUPANT_LAYERS:
            occupant_layer = add_occupant_layer(
                solution=solution,
                venue_group=venue_group,
                qgis_instance_handle=qgis_instance_handle,
            )
            if occupant_layer:
                assert len(occupant_layer) == 1
                occupant_layer = occupant_layer[0]
                occupant_dropdown_widget = make_value_relation_widget(
                    occupant_layer.id(),
                    allow_null_values=True,
                )

        add_building_layers(
            solution=solution,
            progress_bar=progress_bar,
            venue=venue,
            venue_group=venue_group,
            qgis_instance_handle=qgis_instance_handle,
            location_type_ref_layer=location_type_ref_layer,
            location_type_dropdown_widget=location_type_dropdown_widget,
            occupant_dropdown_widget=occupant_dropdown_widget,
        )

        if read_bool_setting("ADD_GRAPH"):  # add graph
            if venue.graph:
                add_graph_layers(
                    graph=venue.graph,
                    venue_group=venue_group,
                    qgis_instance_handle=qgis_instance_handle,
                    solution=solution,
                    venue=venue,
                    highway_type_dropdown_widget=highway_type_dropdown_widget,
                    door_type_dropdown_widget=door_type_dropdown_widget,
                    connection_type_dropdown_widget=connection_type_dropdown_widget,
                    entry_point_type_dropdown_widget=entry_point_type_dropdown_widget,
                    edge_context_type_dropdown_widget=edge_context_type_dropdown_widget,
                )

        if INSERT_INDEX > 0:
            add_venue_polygon_layer(
                qgis_instance_handle, venue, venue_group, venue_type_dropdown_widget
            )


def add_venue_polygon_layer(
    qgis_instance_handle: Any,
    venue: Venue,
    venue_group: Any,
    venue_type_dropdown_widget: Any,
) -> None:
    """

    :param qgis_instance_handle:
    :param venue:
    :param venue_group:
    :param venue_type_dropdown_widget:
    :return:
    """

    venue_layer = add_shapely_layer(
        qgis_instance_handle=qgis_instance_handle,
        geoms=[prepare_geom_for_editing_qgis(venue.polygon)],
        name=VENUE_POLYGON_DESCRIPTOR,
        columns=[
            {
                "admin_id": venue.admin_id,
                "external_id": venue.external_id,
                "last_verified": venue.last_verified,
                "venue_type": venue.venue_type.value,
                **(
                    {
                        f"address.city": venue.address.city,
                        f"address.region": venue.address.region,
                        f"address.country": venue.address.country,
                        f"address.street1": venue.address.street1,
                        f"address.postal_code": venue.address.postal_code,
                        f"address.street2": venue.address.street2,
                    }
                    if venue.address
                    else {}
                ),
                **translations_to_flattened_dict(venue.translations),
            }
        ],
        group=venue_group,
        visible=False,
        crs=solve_target_crs_authid(),
    )
    set_geometry_constraints(venue_layer)

    if venue_type_dropdown_widget:
        for layers_inner in venue_layer:
            if layers_inner:
                if isinstance(layers_inner, Iterable):
                    for layer in layers_inner:
                        if layer:
                            layer.setEditorWidgetSetup(
                                layer.fields().indexFromName("venue_type"),
                                venue_type_dropdown_widget,
                            )
                else:
                    layers_inner.setEditorWidgetSetup(
                        layers_inner.fields().indexFromName("venue_type"),
                        venue_type_dropdown_widget,
                    )
    make_field_unique(venue_layer, field_name="admin_id")
    for field_name in ("name",):
        make_field_not_null(venue_layer, field_name=field_name)

    set_layer_rendering_scale(
        venue_layer,
        min_ratio=read_float_setting("LAYER_GEOM_VISIBLE_MIN_RATIO"),
    )
