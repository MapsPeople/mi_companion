import logging
from typing import Any, Iterable, Optional

from jord.qgis_utilities.fields import make_field_unique
from jord.qlive_utilities import add_shapely_layer

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets

from integration_system.model import Solution, Venue
from mi_companion import (
    ALLOW_DUPLICATE_VENUES_IN_PROJECT,
    DESCRIPTOR_BEFORE,
    VENUE_DESCRIPTOR,
    VENUE_POLYGON_DESCRIPTOR,
)
from mi_companion.configuration.options import read_bool_setting
from mi_companion.constants import (
    INSERT_INDEX,
)
from .building import add_building_layers
from .graph import add_graph_layers
from ...projection import (
    prepare_geom_for_qgis,
    solve_target_crs_authid,
)

logger = logging.getLogger(__name__)

__all__ = ["add_venue_layer"]


def add_venue_layer(
    *,
    qgis_instance_handle: Any,
    solution: Solution,
    solution_group: Any,
    available_location_type_dropdown_widget: Optional[Any] = None,
    door_type_dropdown_widget: Optional[Any] = None,
    highway_type_dropdown_widget: Optional[Any] = None,
    venue_type_dropdown_widget: Optional[Any] = None,
    connection_type_dropdown_widget: Optional[Any] = None,
    progress_bar: Optional[Any] = None,
) -> None:
    if True:
        assert len(solution.venues) > 0, "No venues found"

    for venue in solution.venues:
        if venue is None:
            logger.warning("Venue was None!")
            continue

        if DESCRIPTOR_BEFORE:
            venue_name = f"{VENUE_DESCRIPTOR} {venue.name}"
        else:
            venue_name = f"{venue.name} {VENUE_DESCRIPTOR}"

        venue_group = solution_group.findGroup(venue_name)
        if (
            not ALLOW_DUPLICATE_VENUES_IN_PROJECT
        ):  # TODO: base this in external ids rather than group name
            if venue_group:
                logger.error(f"Venue {venue.name} already loaded!")
                reply = QtWidgets.QMessageBox.question(
                    None,
                    f'f"Venue {venue.name} already loaded!"',
                    f"Would you like to reload the {venue.name} venue from the MI Database?",
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

        add_building_layers(
            solution=solution,
            progress_bar=progress_bar,
            venue=venue,
            venue_group=venue_group,
            qgis_instance_handle=qgis_instance_handle,
            available_location_type_map_widget=available_location_type_dropdown_widget,
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
    venue_layer = add_shapely_layer(
        qgis_instance_handle=qgis_instance_handle,
        geoms=[prepare_geom_for_qgis(venue.polygon)],
        name=VENUE_POLYGON_DESCRIPTOR,
        columns=[
            {
                "admin_id": venue.admin_id,
                "external_id": venue.external_id,
                "name": venue.name,
                "last_verified": venue.last_verified,
                "venue_type": venue.venue_type.name,
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
                **(
                    {
                        f"custom_properties.{lang}.{prop}": str(v)
                        for lang, props_map in venue.custom_properties.items()
                        for prop, v in props_map.items()
                    }
                    if venue.custom_properties
                    else {}
                ),
            }
        ],
        group=venue_group,
        visible=False,
        crs=solve_target_crs_authid(),
    )
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
    make_field_unique(venue_layer)
