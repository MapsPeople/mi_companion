import copy
import logging
import uuid
from itertools import count
from typing import List, Collection

import shapely
from jord.shapely_utilities.base import clean_shape

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets

# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

from integration_system.constants import (
    SHAPELY_DIFFERENCE_DESCRIPTION,
    DIFFERENCE_GROUP_NAME,
)
from integration_system.mi import MIOperation
from integration_system.mi import synchronize
from integration_system.mi.config import Settings
from integration_system.mi.configuration import SyncLevel, SolutionDepth
from integration_system.model import Solution
from mi_companion.configuration.constants import (
    VERBOSE,
    VENUE_POLYGON_DESCRIPTOR,
    GENERATE_MISSING_EXTERNAL_IDS,
    HALF_SIZE,
    CONFIRMATION_DIALOG_ENABLED,
    OPERATION_PROGRESS_BAR_ENABLED,
    SOLVING_PROGRESS_BAR_ENABLED,
    DEFAULT_CUSTOM_PROPERTIES,
    POST_FIT_VENUES,
    POST_FIT_BUILDINGS,
)
from .building import add_building
from .custom_props import extract_custom_props

__all__ = ["convert_venues"]


logger = logging.getLogger(__name__)

# noinspection PyUnresolvedReferences
from qgis.PyQt import QtWidgets, QtCore

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtWidgets import (
    QMessageBox,
)


class ResizableMessageBox(QtWidgets.QMessageBox):  # TODO: MOVE THIS TO JORD!
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSizeGripEnabled(True)

    def event(self, event):
        if event.type() in (event.LayoutRequest, event.Resize):
            if event.type() == event.Resize:
                res = super().event(event)
            else:
                res = False
            details = self.findChild(QtWidgets.QTextEdit)
            if details:
                details.setMaximumSize(16777215, 16777215)
            self.setMaximumSize(16777215, 16777215)
            return res
        return super().event(event)


def convert_venues(
    qgis_instance_handle,
    *,
    solution_group_item: QgsLayerTreeGroup,
    existing_solution: Solution,
    progress_bar: callable,
    solution_external_id: str,
    solution_name: str,
    solution_customer_id: str,
    solution_occupants_enabled: bool,
    settings: Settings,
    ith_solution: int,
    num_solution_elements: int,
    solution_depth=SolutionDepth.LOCATIONS,
    include_route_elements=False,
    include_occupants=False,
    include_media=False,
    include_graph=False,
) -> None:
    venue_elements = solution_group_item.children()
    num_venue_elements = len(venue_elements)
    for ith_venue, venue_group_items in enumerate(venue_elements):
        if not isinstance(venue_group_items, QgsLayerTreeGroup):
            continue  # Selected the solution_data object

        if progress_bar:
            progress_bar.setValue(
                int(
                    10
                    + (
                        90
                        * ((ith_solution + HALF_SIZE) / num_solution_elements)
                        * ((ith_venue + HALF_SIZE) / num_venue_elements)
                    )
                )
            )

        if existing_solution is None:
            solution = Solution(
                solution_external_id,
                solution_name,
                solution_customer_id,
                occupants_enabled=solution_occupants_enabled,
            )
        else:
            solution = copy.deepcopy(existing_solution)

        venue_key = None
        for building_group_items in venue_group_items.children():
            layer_type_test = isinstance(building_group_items, QgsLayerTreeLayer)
            layer_name = str(building_group_items.name()).lower()
            layer_descriptor_test = VENUE_POLYGON_DESCRIPTOR.lower() in layer_name

            if layer_type_test and layer_descriptor_test:
                assert venue_key is None, f"{venue_key=} was already set"
                venue_polygon_layer = building_group_items.layer()
                venue_feature = venue_polygon_layer.getFeature(1)  # 1 is first element

                venue_attributes = {
                    k.name(): v
                    for k, v in zip(venue_feature.fields(), venue_feature.attributes())
                }

                if len(venue_attributes) == 0:
                    continue
                else:
                    logger.error(
                        f"Did not find venue, skipping {building_group_items.name()}"
                    )

                external_id = venue_attributes["external_id"]
                if external_id is None:
                    if GENERATE_MISSING_EXTERNAL_IDS:
                        external_id = uuid.uuid4().hex
                    else:
                        raise ValueError(
                            f"{venue_feature} is missing a valid external id"
                        )

                name = venue_attributes["name"]
                if name is None:
                    name = external_id

                custom_props = extract_custom_props(venue_attributes)

                venue_key = solution.add_venue(
                    external_id=external_id,
                    name=name,
                    polygon=clean_shape(
                        shapely.from_wkt(venue_feature.geometry().asWkt())
                    ),
                    custom_properties=(
                        custom_props if custom_props else DEFAULT_CUSTOM_PROPERTIES
                    ),
                )

        if venue_key:
            add_building(
                ith_solution,
                ith_venue,
                num_solution_elements,
                num_venue_elements,
                progress_bar,
                solution,
                venue_group_items,
                venue_key,
            )

            """if False:
                existing_venue_solution = get_remote_solution(
                    solution_name,
                    venue_keys=[venue_key],
                    settings=settings,
                    include_graph=False,
                )
                if existing_venue_solution:
                    for occupant in existing_solution.occupants:
                        solution.add_occupant(
                            location_key=occupant.location.key,
                            occupant_template_key=(
                                occupant.template.key if occupant.template else None
                            ),
                            is_anchor=occupant.is_anchor,
                            is_operating=occupant.is_operating,
                            aliases=occupant.aliases,
                            business_hours=occupant.business_hours,
                            address=occupant.address,
                            contact=occupant.contact,
                            media_key=(occupant.logo.key if occupant.logo else None),
                        )"""
        else:
            f"Did not find a {venue_key=}, skipping"

        if VERBOSE:
            logger.info("Synchronising")

        # TODO: REVISE BUILDING -> VENUE POLYGONS TO FIT FLOOR POLYGONS!
        # WITH UPDATES
        if POST_FIT_BUILDINGS:
            ...
            # solution.update_building(key=None,polygon=None)

        if POST_FIT_VENUES:
            ...
            # solution.update_venue(key=None,polygon=None)

        def solving_progress_bar_callable(ith: int, total: int) -> None:
            progress_bar.setValue(int(20 + (ith / total) * 80))
            logger.debug(f"Solving: {ith}/{total}")

        def operation_progress_bar_callable(
            operation: MIOperation, ith: int, total: int
        ) -> None:
            progress_bar.setValue(int(20 + (ith / total) * 80))
            logger.debug(operation)
            logger.debug(f"Synchronising: {ith}/{total}")

            # qgis_instance_handle.iface.messageBar().popWidget()
            # qgis_instance_handle.iface.messageBar().pushMessage(before, text, level=level, duration=duration)

        def confirmation_dialog(operations: List[MIOperation]) -> bool:
            window_title = f"Sync {solution_name} Venues"

            if operations is None or len(operations) == 0:
                QMessageBox.information(
                    None, window_title, "No difference was found, no operations"
                )
                return False

            def aggregate_operation_description(
                operation: Collection[MIOperation],
            ) -> str:
                desc = ""
                for o in operation:
                    desc += f"{o.operation_type.name}: {len(o.object_keys)} {o.object_type.__name__}(s)\n"

                return desc

            msg_box = ResizableMessageBox(
                # parent=qgis_instance_handle.iface
            )
            msg_box.setWindowFlags(
                QtCore.Qt.Dialog  # & ~QtCore.Qt.MSWindowsFixedSizeDialogHint
            )
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle(window_title)
            msg_box.setText(f"The {solution_name} venue(s) has been modified.")
            msg_box.setInformativeText(
                f"Do you want to sync following changes?\n\n{aggregate_operation_description(operations)}"
            )
            msg_box.setDetailedText("\n\n".join([str(o) for o in operations]))
            msg_box.setStandardButtons(
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Help
            )
            msg_box.setDefaultButton(QMessageBox.No)
            msg_box.setEscapeButton(QMessageBox.No)
            reply = msg_box.exec()

            if reply == QMessageBox.Yes:
                return True

            if reply == QMessageBox.Help:
                show_differences(
                    qgis_instance_handle=qgis_instance_handle,
                    solution=solution,
                    solution_name=solution_name,
                    operations=operations,
                )

            return False

        synchronize(
            solution,
            sync_level=SyncLevel.VENUE,
            settings=settings,
            operation_progress_callback=(
                operation_progress_bar_callable
                if OPERATION_PROGRESS_BAR_ENABLED
                else None
            ),
            solving_progress_callback=(
                solving_progress_bar_callable if SOLVING_PROGRESS_BAR_ENABLED else None
            ),
            confirmation_callback=(
                confirmation_dialog if CONFIRMATION_DIALOG_ENABLED else None
            ),
            depth=solution_depth,
            include_route_elements=include_route_elements,
            include_occupants=include_occupants,
            include_media=include_media,
            include_graph=include_graph,
        )

        if VERBOSE:
            logger.info("Synchronised")


def show_differences(
    *, qgis_instance_handle, solution, solution_name, operations
) -> None:
    mi_db_difference_group = (
        QgsProject.instance().layerTreeRoot().findGroup(DIFFERENCE_GROUP_NAME)
    )

    if not mi_db_difference_group:  # did not find the group
        mi_db_difference_group = (
            QgsProject.instance().layerTreeRoot().insertGroup(0, DIFFERENCE_GROUP_NAME)
        )

    solution_difference_group = mi_db_difference_group.findGroup(solution_name)

    if not solution_difference_group:  # did not find the group
        solution_difference_group = mi_db_difference_group.insertGroup(0, solution_name)

    venue = next(iter(solution.venues))
    venue_diff_name = venue.name

    venue_difference_group = solution_difference_group.findGroup(venue_diff_name)

    if venue_difference_group:  # Found the group
        for node in [
            child
            for child in venue_difference_group.children()
            # if child.nodeType() == 0
        ]:
            venue_difference_group.removeChildNode(node)
    else:  # did not find the group
        venue_difference_group = solution_difference_group.insertGroup(
            0, venue_diff_name
        )

    for o in operations:
        differences = {}
        operation_counter = iter(count())
        from jord.shapely_utilities import is_multi

        if SHAPELY_DIFFERENCE_DESCRIPTION in o.context:
            for i in o.context.split(SHAPELY_DIFFERENCE_DESCRIPTION)[1:]:
                diff_op_ith = next(
                    operation_counter
                )  # TODO: ALL OF THIS CAN BE IMPROVED! WITH SOME proper IDs

                differences[diff_op_ith] = shapely.from_wkt(
                    i.split("\n")[0].strip("\n").strip()
                )  # Also one parses a single geom per operation
                if is_multi(differences[diff_op_ith]):
                    rep_points = []
                    for g in differences[diff_op_ith].geoms:
                        rep_points.append(g.representative_point())
                    differences[f"{diff_op_ith}_coherence"] = shapely.LineString(
                        rep_points
                    )

        try:
            import geopandas

            df = geopandas.GeoDataFrame(
                {"op_ith": differences.keys(), "geometry": differences.values()},
                crs="EPSG:3857",
                geometry="geometry",
            )
            from jord.qlive_utilities import add_dataframe_layer

            add_dataframe_layer(
                qgis_instance_handle=qgis_instance_handle,
                dataframe=df,
                geometry_column="geometry",
                name=f"{o.object_type.__name__} differences",
                group=venue_difference_group,
            )
        except Exception as e:  # TODO: HANDLE MIxed GEOM TYPES!
            logger.error(e)
