"""
Example: Comparing Graphs Using NetworkX Difference Analysis

This sample demonstrates how to use the enhanced Graph class methods
to analyze and display differences between two graph instances.
"""

from sync_module.model.graph import (
    Graph,
)
from sync_module.tools.graph_utilities.graph_difference import (
    analyze_graph_difference_detailed,
    explain_difference,
    format_difference_report,
)


def example_1_simple_metrics():
    """
    Example 1: Get basic difference metrics between two graphs.

    Shows how to access simple metrics like node count, edge count, and density.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Simple Difference Metrics")
    print("=" * 80)

    # Create two sample graphs with different structures
    graph1 = Graph(
        graph_id="building_floor_2",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1">
    <tag k="level" v="2" />
  </node>
  <node id="2" lat="1.0" lon="1.0" version="1">
    <tag k="level" v="2" />
  </node>
  <node id="3" lat="2.0" lon="2.0" version="1">
    <tag k="level" v="2" />
  </node>
  <node id="4" lat="3.0" lon="3.0" version="1">
    <tag k="level" v="2" />
  </node>
  <node id="5" lat="4.0" lon="4.0" version="1">
    <tag k="level" v="2" />
  </node>
  <way id="101" version="1">
    <nd ref="1" />
    <nd ref="2" />
    <tag k="indoor" v="yes" />
    <tag k="highway" v="footway" />
  </way>
  <way id="102" version="1">
    <nd ref="2" />
    <nd ref="3" />
    <tag k="indoor" v="yes" />
    <tag k="highway" v="footway" />
  </way>
  <way id="103" version="1">
    <nd ref="3" />
    <nd ref="4" />
    <tag k="indoor" v="yes" />
    <tag k="highway" v="footway" />
  </way>
  <way id="104" version="1">
    <nd ref="4" />
    <nd ref="5" />
    <tag k="indoor" v="yes" />
    <tag k="highway" v="footway" />
  </way>
  <way id="105" version="1">
    <nd ref="5" />
    <nd ref="1" />
    <tag k="indoor" v="yes" />
    <tag k="highway" v="footway" />
  </way>
</osm>""",
    )

    # Second graph with slightly different structure (one less node and edge)
    graph2 = Graph(
        graph_id="building_floor_2",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1">
    <tag k="level" v="2" />
  </node>
  <node id="2" lat="1.0" lon="1.0" version="1">
    <tag k="level" v="2" />
  </node>
  <node id="3" lat="2.0" lon="2.0" version="1">
    <tag k="level" v="2" />
  </node>
  <node id="4" lat="3.0" lon="3.0" version="1">
    <tag k="level" v="2" />
  </node>
  <way id="101" version="1">
    <nd ref="1" />
    <nd ref="2" />
    <tag k="indoor" v="yes" />
    <tag k="highway" v="footway" />
  </way>
  <way id="102" version="1">
    <nd ref="2" />
    <nd ref="3" />
    <tag k="indoor" v="yes" />
    <tag k="highway" v="footway" />
  </way>
  <way id="103" version="1">
    <nd ref="3" />
    <nd ref="4" />
    <tag k="indoor" v="yes" />
    <tag k="highway" v="footway" />
  </way>
  <way id="104" version="1">
    <nd ref="4" />
    <nd ref="1" />
    <tag k="indoor" v="yes" />
    <tag k="highway" v="footway" />
  </way>
</osm>""",
    )

    # Get basic metrics
    try:
        metrics = graph1.get_graph_difference_metrics(graph2)

        print("\nBasic Metrics Comparison:")
        print("-" * 80)
        print(
            f"Nodes:      Graph1: {metrics['structure']['nodes']['self']:3d}  |  "
            f"Graph2: {metrics['structure']['nodes']['other']:3d}  |  "
            f"Difference: {metrics['structure']['nodes']['difference']:+d}"
        )
        print(
            f"Edges:      Graph1: {metrics['structure']['edges']['self']:3d}  |  "
            f"Graph2: {metrics['structure']['edges']['other']:3d}  |  "
            f"Difference: {metrics['structure']['edges']['difference']:+d}"
        )
        print(
            f"Density:    Graph1: {metrics['structure']['density']['self']:6.4f}  |  "
            f"Graph2: {metrics['structure']['density']['other']:6.4f}  |  "
            f"Difference: {metrics['structure']['density']['difference']:+.4f}"
        )
        print(f"Isomorphic: {metrics['isomorphic']}")

    except Exception as e:
        print(f"Error: {e}")


def example_2_quick_explanation():
    """
    Example 2: Get a quick human-readable explanation of differences.

    Perfect for logging or quick diagnostics.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Quick Difference Explanation")
    print("=" * 80)

    # Using same graphs as Example 1
    graph1 = Graph(
        graph_id="venue_map_v1",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="4" lat="3.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
  <way id="2" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="footway" /></way>
  <way id="3" version="1"><nd ref="3" /><nd ref="4" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    graph2 = Graph(
        graph_id="venue_map_v1",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
  <way id="2" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    try:
        explanation = explain_difference(graph1, graph2)
        print(f"\nDifference Summary:\n{explanation}")
    except Exception as e:
        print(f"Error: {e}")


def example_3_detailed_analysis():
    """
    Example 3: Get detailed structural analysis using networkx algorithms.

    Shows comprehensive analysis including centrality measures, clustering, etc.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Detailed Structural Analysis")
    print("=" * 80)

    graph1 = Graph(
        graph_id="building_floor_1",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="4" lat="3.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="5" lat="1.0" lon="1.0" version="1"><tag k="level" v="1" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
  <way id="2" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="footway" /></way>
  <way id="3" version="1"><nd ref="3" /><nd ref="4" /><tag k="highway" v="footway" /></way>
  <way id="4" version="1"><nd ref="2" /><nd ref="5" /><tag k="highway" v="footway" /></way>
  <way id="5" version="1"><nd ref="5" /><nd ref="3" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    graph2 = Graph(
        graph_id="building_floor_1",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="4" lat="3.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
  <way id="2" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="footway" /></way>
  <way id="3" version="1"><nd ref="3" /><nd ref="4" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    try:
        analysis = analyze_graph_difference_detailed(graph1, graph2)

        print("\nDetailed Analysis Summary:")
        print("-" * 80)
        print(f"Graphs Isomorphic: {analysis['summary']['graphs_isomorphic']}")
        print(f"Structure Differs:  {analysis['summary']['structure_differs']}")

        print("\nGraph 1 Structure:")
        print(f"  Nodes: {analysis['self']['structure']['nodes']}")
        print(f"  Edges: {analysis['self']['structure']['edges']}")
        print(f"  Directed: {analysis['self']['structure']['is_directed']}")

        if "degree_distribution" in analysis["self"]:
            print(
                f"  Degree - Min: {analysis['self']['degree_distribution']['min']:.2f}, "
                f"Max: {analysis['self']['degree_distribution']['max']:.2f}, "
                f"Avg: {analysis['self']['degree_distribution']['avg']:.2f}"
            )

        if "density_metrics" in analysis["self"]:
            print(
                f"  Density: {analysis['self']['density_metrics']['density']:.4f}, "
                f"Transitivity: {analysis['self']['density_metrics']['transitivity']:.4f}"
            )

        print("\nGraph 2 Structure:")
        print(f"  Nodes: {analysis['other']['structure']['nodes']}")
        print(f"  Edges: {analysis['other']['structure']['edges']}")
        print(f"  Directed: {analysis['other']['structure']['is_directed']}")

        if "degree_distribution" in analysis["other"]:
            print(
                f"  Degree - Min: {analysis['other']['degree_distribution']['min']:.2f}, "
                f"Max: {analysis['other']['degree_distribution']['max']:.2f}, "
                f"Avg: {analysis['other']['degree_distribution']['avg']:.2f}"
            )

        if "density_metrics" in analysis["other"]:
            print(
                f"  Density: {analysis['other']['density_metrics']['density']:.4f}, "
                f"Transitivity: {analysis['other']['density_metrics']['transitivity']:.4f}"
            )

        if "degree_comparison" in analysis:
            print("\nDegree Distribution Differences:")
            print(
                f"  Min Degree Diff: {analysis['degree_comparison']['min_degree_diff']:+.2f}"
            )
            print(
                f"  Max Degree Diff: {analysis['degree_comparison']['max_degree_diff']:+.2f}"
            )
            print(
                f"  Avg Degree Diff: {analysis['degree_comparison']['avg_degree_diff']:+.2f}"
            )

    except Exception as e:
        print(f"Error: {e}")


def example_4_formatted_report():
    """
    Example 4: Generate a comprehensive formatted difference report.

    Perfect for displaying in UI or writing to logs.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Formatted Difference Report")
    print("=" * 80)

    graph1 = Graph(
        graph_id="building_map_v2",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="2" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="2" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="level" v="2" /></node>
  <node id="4" lat="3.0" lon="0.0" version="1"><tag k="level" v="2" /></node>
  <node id="5" lat="4.0" lon="0.0" version="1"><tag k="level" v="2" /></node>
  <node id="6" lat="1.0" lon="1.0" version="1"><tag k="level" v="2" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
  <way id="2" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="footway" /></way>
  <way id="3" version="1"><nd ref="3" /><nd ref="4" /><tag k="highway" v="footway" /></way>
  <way id="4" version="1"><nd ref="4" /><nd ref="5" /><tag k="highway" v="footway" /></way>
  <way id="5" version="1"><nd ref="2" /><nd ref="6" /><tag k="highway" v="footway" /></way>
  <way id="6" version="1"><nd ref="6" /><nd ref="4" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    graph2 = Graph(
        graph_id="building_map_v2",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="2" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="2" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="level" v="2" /></node>
  <node id="4" lat="3.0" lon="0.0" version="1"><tag k="level" v="2" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
  <way id="2" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="footway" /></way>
  <way id="3" version="1"><nd ref="3" /><nd ref="4" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    try:
        report = format_difference_report(graph1, graph2)
        print(report)
    except Exception as e:
        print(f"Error: {e}")


def example_5_equality_check():
    """
    Example 5: Using the enhanced __eq__ method for graph comparison.

    Shows how the isomorphism-based equality checking works.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Graph Equality (Isomorphism) Check")
    print("=" * 80)

    # Two graphs with identical structure but different node IDs
    # (same logical structure, different XML representation)
    graph1 = Graph(
        graph_id="venue_path",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="100" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="101" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="102" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="1" version="1"><nd ref="100" /><nd ref="101" /><tag k="highway" v="footway" /></way>
  <way id="2" version="1"><nd ref="101" /><nd ref="102" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    graph2 = Graph(
        graph_id="venue_path",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="10" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
  <way id="20" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    try:
        are_equal = graph1 == graph2
        print(f"\nGraphs equal (isomorphic): {are_equal}")
        print(f"  Same IDs: {graph1.graph_id == graph2.graph_id}")
        print(f"  Same XML: {graph1.osm_xml == graph2.osm_xml}")
        print(f"  -> Despite different XML, they have the same logical structure!")
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("GRAPH DIFFERENCE ANALYSIS - COMPREHENSIVE EXAMPLES")
    print("=" * 80)

    try:
        example_1_simple_metrics()
    except Exception as e:
        print(f"Example 1 failed: {e}")

    try:
        example_2_quick_explanation()
    except Exception as e:
        print(f"Example 2 failed: {e}")

    try:
        example_3_detailed_analysis()
    except Exception as e:
        print(f"Example 3 failed: {e}")

    try:
        example_4_formatted_report()
    except Exception as e:
        print(f"Example 4 failed: {e}")

    try:
        example_5_equality_check()
    except Exception as e:
        print(f"Example 5 failed: {e}")

    print("\n" + "=" * 80)
    print("All examples completed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
