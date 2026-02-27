"""
Example QGIS Plugin Entry Point for Validating Graph with UI Feedback

This example demonstrates how to integrate the problematic edges UI
into a QGIS plugin entry point that validates imported data.
"""

import logging
from typing import Optional

_logger = logging.getLogger(__name__)


def run() -> None:
    """
    Validate graph edges and present any issues in a clickable UI list.

    This function can be called from a QGIS plugin menu or toolbar button.
    It demonstrates the complete workflow for:
    1. Loading or creating a graph
    2. Validating the graph for problematic edges
    3. Presenting results in a user-friendly QGIS dialog
    """
    try:
        from qgis.utils import iface
        from sync_module.tools.graph_utilities import (
            validate_vertical_lines,
            present_problematic_edges_ui,
        )

        _logger.info("Starting graph validation process...")

        # Step 1: Get the graph to validate
        # This is a placeholder - your actual implementation would:
        # - Load from a layer
        # - Import from file
        # - Create from features
        graph = get_graph_for_validation()

        if graph is None:
            iface.messageBar().pushMessage(
                "Error",
                "Could not load graph for validation. Please select a valid source.",
                level=2,
            )
            return

        # Step 2: Validate the graph
        _logger.info(
            f"Validating graph with {graph.number_of_nodes()} nodes "
            f"and {graph.number_of_edges()} edges..."
        )

        problematic_edges = validate_vertical_lines(graph)

        _logger.info(f"Validation complete. Found {len(problematic_edges)} issue(s)")

        # Step 3: Present results to the user
        if problematic_edges:
            # Show issues in clickable UI
            _logger.warning(f"{len(problematic_edges)} problematic edges found")
            present_problematic_edges_ui(problematic_edges)
        else:
            # Show success message
            iface.messageBar().pushMessage(
                "Success",
                "Graph validation complete - no issues found!",
                level=0,  # Info level
            )
            _logger.info("Graph validation successful - all edges properly connected")

    except ImportError as e:
        _logger.error(f"QGIS modules not available: {e}")
        _logger.error("This function must be called from within a QGIS environment")
    except Exception as e:
        _logger.exception(f"Unexpected error during validation: {e}")
        try:
            from qgis.utils import iface

            iface.messageBar().pushMessage(
                "Error",
                f"Validation failed: {str(e)}",
                level=2,
            )
        except:
            pass


def get_graph_for_validation():
    """
    Load or create a graph for validation.

    This is a placeholder that should be implemented based on your
    specific use case. Examples:

    - Load from a QGIS layer
    - Import from shapefile/GeoPackage
    - Generate from 3D LineString data
    - Load from OSM XML

    Returns:
        MultiDiGraph: The graph to validate, or None if unavailable
    """
    try:
        from qgis.utils import iface
        from qgis.core import QgsVectorLayer

        # Example: Load from active layer
        layer = iface.activeLayer()
        if layer is None:
            _logger.error("No active layer selected")
            return None

        if not isinstance(layer, QgsVectorLayer):
            _logger.error("Active layer must be a vector layer")
            return None

        # Here you would convert the layer to a graph
        # This is application-specific and depends on your data structure
        # For now, return None as a placeholder
        _logger.warning("Graph loading not implemented - returning None")
        return None

    except ImportError:
        _logger.error("QGIS not available in this context")
        return None


def batch_validate_graphs(layer_names: list) -> None:
    """
    Validate multiple graphs and collect results.

    This example shows how to validate multiple layers and aggregate
    the results into a single report.

    Args:
        layer_names: List of QGIS layer names to validate
    """
    try:
        from qgis.utils import iface
        from qgis.core import QgsProject
        from sync_module.tools.graph_utilities import validate_vertical_lines

        all_problematic_edges = []
        validation_results = {}

        for layer_name in layer_names:
            # Get layer by name
            layer = QgsProject.instance().mapLayersByName(layer_name)
            if not layer:
                _logger.warning(f"Layer '{layer_name}' not found")
                continue

            # Load graph from layer
            graph = load_graph_from_layer(layer[0])
            if graph is None:
                continue

            # Validate
            problematic_edges = validate_vertical_lines(graph)
            validation_results[layer_name] = problematic_edges
            all_problematic_edges.extend(problematic_edges)

        # Report results
        _logger.info(f"\n=== Batch Validation Results ===")
        for layer_name, issues in validation_results.items():
            _logger.info(f"{layer_name}: {len(issues)} issue(s)")

        _logger.info(f"Total problematic edges: {len(all_problematic_edges)}")

        # Show in UI if there are issues
        if all_problematic_edges:
            from sync_module.tools.graph_utilities import present_problematic_edges_ui

            present_problematic_edges_ui(all_problematic_edges)

    except Exception as e:
        _logger.exception(f"Error during batch validation: {e}")


def load_graph_from_layer(layer):
    """
    Placeholder for converting a QGIS layer to a graph.

    This would typically involve:
    1. Extracting features from the layer
    2. Converting geometries to nodes
    3. Building edges from relationships
    4. Adding attributes to nodes and edges

    Args:
        layer: QGIS QgsVectorLayer

    Returns:
        MultiDiGraph: The converted graph, or None if conversion fails
    """
    _logger.warning("load_graph_from_layer not implemented")
    return None


# Example: Register as QGIS Plugin Action
def setup_menu_action(iface):
    """
    Register this function as a QGIS menu action.

    This would typically be called from the plugin's initGui() method.

    Args:
        iface: QGIS interface instance
    """
    from qgis.PyQt.QtWidgets import QAction
    from qgis.PyQt.QtGui import QIcon

    action = QAction("Validate Graph Edges", iface.mainWindow())
    action.triggered.connect(run)

    # Add to menu
    iface.addPluginToMenu("&My Plugin", action)

    # Optionally add to toolbar
    # iface.addToolBarIcon(action)

    return action


if __name__ == "__main__":
    # This can be run from QGIS Python console or as a standalone test
    print("This module is designed to be imported and used within QGIS")
    print("Run run() function from QGIS Python console to validate a graph")
