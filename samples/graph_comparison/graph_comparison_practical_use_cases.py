"""
Practical Use Case: Graph Validation During Migration/Transformation

This example shows real-world scenarios where graph comparison is useful:
1. Validating graph transformations
2. Detecting unintended changes
3. Quality assurance in data pipeline
"""

from sync_module.model.graph import (
    Graph,
)
from sync_module.tools.graph_utilities.graph_difference import (
    explain_difference,
    get_graph_difference_metrics,
)
from typing import Tuple, Optional
import json


class GraphMigrationValidator:
    """
    Validates that graph transformations don't introduce unexpected changes.
    Useful in data pipelines and migration scripts.
    """

    def __init__(self, tolerance: float = 0.05):
        """
        Initialize validator with tolerance threshold.

        Args:
            tolerance: Acceptable difference in metrics (5% by default)
        """
        self.tolerance = tolerance
        self.validation_results = []

    def validate_transformation(
        self,
        original: Graph,
        transformed: Graph,
        expected_node_change: Optional[int] = None,
        expected_edge_change: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """
        Validate that a graph transformation is reasonable.

        Args:
            original: Original graph before transformation
            transformed: Graph after transformation
            expected_node_change: Expected number of nodes to add/remove (if known)
            expected_edge_change: Expected number of edges to add/remove (if known)

        Returns:
            Tuple of (is_valid, detailed_message)
        """
        try:
            metrics = original.get_graph_difference_metrics(transformed)
        except Exception as e:
            return False, f"Failed to analyze graphs: {e}"

        issues = []
        warnings = []

        # Check node changes
        node_diff = metrics["structure"]["nodes"]["difference"]
        if expected_node_change is not None:
            if abs(node_diff - expected_node_change) > 1:
                issues.append(
                    f"Unexpected node change: expected {expected_node_change:+d}, "
                    f"got {node_diff:+d}"
                )
        elif abs(node_diff) > 10:  # Arbitrary threshold
            warnings.append(f"Large node change: {node_diff:+d} nodes")

        # Check edge changes
        edge_diff = metrics["structure"]["edges"]["difference"]
        if expected_edge_change is not None:
            if abs(edge_diff - expected_edge_change) > 1:
                issues.append(
                    f"Unexpected edge change: expected {expected_edge_change:+d}, "
                    f"got {edge_diff:+d}"
                )
        elif abs(edge_diff) > 10:  # Arbitrary threshold
            warnings.append(f"Large edge change: {edge_diff:+d} edges")

        # Check for disconnection when graph should remain connected
        orig_connected = metrics["connectivity"]["is_connected_self"]
        trans_connected = metrics["connectivity"]["is_connected_other"]

        if orig_connected and not trans_connected:
            issues.append("Graph became disconnected during transformation!")

        component_diff = (
            metrics["connectivity"]["num_components_other"]
            - metrics["connectivity"]["num_components_self"]
        )
        if component_diff > 0:
            warnings.append(f"Number of components increased by {component_diff}")

        # Check density changes
        density_diff = metrics["structure"]["density"]["difference"]
        if abs(density_diff) > self.tolerance:
            warnings.append(
                f"Significant density change: {density_diff:+.4f} "
                f"({metrics['structure']['density']['self']:.4f} -> "
                f"{metrics['structure']['density']['other']:.4f})"
            )

        # Compile results
        is_valid = len(issues) == 0
        message_parts = []

        if is_valid:
            message_parts.append("✓ Transformation validation passed")
        else:
            message_parts.append(f"✗ Validation FAILED with {len(issues)} issue(s):")
            for issue in issues:
                message_parts.append(f"  - {issue}")

        if warnings:
            message_parts.append(f"\n⚠ {len(warnings)} warning(s):")
            for warning in warnings:
                message_parts.append(f"  - {warning}")

        message = "\n".join(message_parts)
        self.validation_results.append(
            {
                "valid": is_valid,
                "message": message,
                "metrics": metrics,
                "issues": issues,
                "warnings": warnings,
            }
        )

        return is_valid, message


class GraphComparisonReporter:
    """
    Generates detailed reports comparing multiple graph versions.
    Useful for tracking changes over time or comparing multiple implementations.
    """

    def __init__(self):
        self.comparisons = []

    def add_comparison(self, name: str, graph1: Graph, graph2: Graph):
        """Add a graph pair comparison to the report."""
        try:
            metrics = get_graph_difference_metrics(graph1, graph2)
            explanation = explain_difference(graph1, graph2)

            self.comparisons.append(
                {
                    "name": name,
                    "graph1_id": graph1.graph_id,
                    "graph2_id": graph2.graph_id,
                    "metrics": metrics,
                    "explanation": explanation,
                }
            )
        except Exception as e:
            self.comparisons.append({"name": name, "error": str(e)})

    def generate_json_report(self) -> str:
        """Generate JSON report of all comparisons."""
        return json.dumps(self.comparisons, indent=2, default=str)

    def generate_text_report(self) -> str:
        """Generate human-readable text report."""
        lines = []
        lines.append("=" * 80)
        lines.append("GRAPH COMPARISON REPORT")
        lines.append("=" * 80)
        lines.append(f"\nTotal Comparisons: {len(self.comparisons)}\n")

        for i, comp in enumerate(self.comparisons, 1):
            lines.append(f"\n[Comparison {i}] {comp['name']}")
            lines.append("-" * 80)

            if "error" in comp:
                lines.append(f"ERROR: {comp['error']}")
                continue

            lines.append(f"Graph 1: {comp['graph1_id']}")
            lines.append(f"Graph 2: {comp['graph2_id']}")
            lines.append(f"\nSummary: {comp['explanation']}")

            metrics = comp["metrics"]
            lines.append(f"\nMetrics:")
            lines.append(
                f"  Nodes:      {metrics['structure']['nodes']['self']:3d} -> "
                f"{metrics['structure']['nodes']['other']:3d} "
                f"(Δ {metrics['structure']['nodes']['difference']:+d})"
            )
            lines.append(
                f"  Edges:      {metrics['structure']['edges']['self']:3d} -> "
                f"{metrics['structure']['edges']['other']:3d} "
                f"(Δ {metrics['structure']['edges']['difference']:+d})"
            )
            lines.append(
                f"  Density:    {metrics['structure']['density']['self']:.4f} -> "
                f"{metrics['structure']['density']['other']:.4f} "
                f"(Δ {metrics['structure']['density']['difference']:+.4f})"
            )
            lines.append(f"  Isomorphic: {metrics['isomorphic']}")

        lines.append("\n" + "=" * 80)
        return "\n".join(lines)


def use_case_1_migration_validation():
    """
    Use Case 1: Validate that a graph transformation doesn't break structure.

    Scenario: You're migrating from one graph format to another and want to
    ensure the new format preserves the graph structure.
    """
    print("\n" + "=" * 80)
    print("USE CASE 1: Migration Validation")
    print("=" * 80)

    original = Graph(
        graph_id="venue_v1",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
  <way id="2" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    transformed = Graph(
        graph_id="venue_v1",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
  <way id="2" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    validator = GraphMigrationValidator()
    is_valid, message = validator.validate_transformation(
        original, transformed, expected_node_change=0, expected_edge_change=0
    )

    print(f"\n{message}")


def use_case_2_quality_assurance():
    """
    Use Case 2: QA testing to ensure graph modifications meet expectations.

    Scenario: A processing step should add/remove specific nodes/edges.
    Validate that it does so correctly.
    """
    print("\n" + "=" * 80)
    print("USE CASE 2: Quality Assurance Testing")
    print("=" * 80)

    original = Graph(
        graph_id="floor_1",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
  <way id="2" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    # After processing, we expect to add 2 more nodes and 2 more edges
    processed = Graph(
        graph_id="floor_1",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="4" lat="3.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="5" lat="4.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
  <way id="2" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="footway" /></way>
  <way id="3" version="1"><nd ref="3" /><nd ref="4" /><tag k="highway" v="footway" /></way>
  <way id="4" version="1"><nd ref="4" /><nd ref="5" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    validator = GraphMigrationValidator()
    is_valid, message = validator.validate_transformation(
        original,
        processed,
        expected_node_change=2,  # We expect 2 new nodes
        expected_edge_change=2,  # We expect 2 new edges
    )

    print(f"\n{message}")


def use_case_3_multi_version_comparison():
    """
    Use Case 3: Compare multiple versions of a graph over time.

    Scenario: Track how a building's indoor map evolves across versions,
    comparing all versions to understand structural changes.
    """
    print("\n" + "=" * 80)
    print("USE CASE 3: Multi-Version Comparison Report")
    print("=" * 80)

    version_1 = Graph(
        graph_id="building_map_v1",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    version_2 = Graph(
        graph_id="building_map_v2",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
  <way id="2" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    reporter = GraphComparisonReporter()
    reporter.add_comparison("v1 vs v2", version_1, version_2)
    reporter.add_comparison("v2 vs v1", version_2, version_1)

    print("\nText Report:")
    print(reporter.generate_text_report())

    print("\nJSON Report:")
    print(reporter.generate_json_report())


def main():
    """Run all practical use cases."""
    try:
        use_case_1_migration_validation()
    except Exception as e:
        print(f"Use case 1 failed: {e}")

    try:
        use_case_2_quality_assurance()
    except Exception as e:
        print(f"Use case 2 failed: {e}")

    try:
        use_case_3_multi_version_comparison()
    except Exception as e:
        print(f"Use case 3 failed: {e}")

    print("\n" + "=" * 80)
    print("All use cases completed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
