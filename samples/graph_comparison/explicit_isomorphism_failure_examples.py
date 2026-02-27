"""
Example: Explicit Isomorphism Failure Descriptions

This example demonstrates the enhanced isomorphism failure messages
that provide EXPLICIT, DETAILED structural reasons for why graphs cannot be isomorphic.
"""

from sync_module.model.graph import Graph
from sync_module.tools.graph_utilities.graph_difference import explain_difference


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def example_1_node_count_mismatch():
    """
    EXPLICIT: Different number of nodes
    WHY: One graph has 5 nodes, the other has 3 nodes
    CONSEQUENCE: Impossible to map nodes between graphs
    """
    print_section("EXAMPLE 1: Node Count Mismatch")

    graph1 = Graph(
        graph_id="test",
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

    graph2 = Graph(
        graph_id="test",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
  <way id="2" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    print("\nGraph 1: Linear path with 5 nodes (1-2-3-4-5)")
    print("Graph 2: Linear path with 3 nodes (1-2-3)")
    print("\nDifference Explanation:")
    print(explain_difference(graph1, graph2))


def example_2_edge_count_mismatch():
    """
    EXPLICIT: Different number of edges
    WHY: One graph has 3 edges, the other has 2 edges
    CONSEQUENCE: Different connectivity - one is more sparse than the other
    """
    print_section("EXAMPLE 2: Edge Count Mismatch (Same Nodes)")

    graph1 = Graph(
        graph_id="test",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
  <way id="2" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="footway" /></way>
  <way id="3" version="1"><nd ref="1" /><nd ref="3" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    graph2 = Graph(
        graph_id="test",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
  <way id="2" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    print("\nGraph 1: Triangle (3 nodes, 3 edges, fully connected)")
    print("Graph 2: Linear path (3 nodes, 2 edges, sparsely connected)")
    print("\nDifference Explanation:")
    print(explain_difference(graph1, graph2))


def example_3_degree_sequence_mismatch():
    """
    EXPLICIT: Different degree sequences
    WHY: One graph has a hub node (degree 3), the other is a simple path (max degree 2)
    CONSEQUENCE: Nodes have different connectivity patterns - cannot map
    """
    print_section("EXAMPLE 3: Degree Sequence Mismatch")

    graph1 = Graph(
        graph_id="test",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="4" lat="3.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="1" version="1"><nd ref="2" /><nd ref="1" /><tag k="highway" v="footway" /></way>
  <way id="2" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="footway" /></way>
  <way id="3" version="1"><nd ref="2" /><nd ref="4" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    graph2 = Graph(
        graph_id="test",
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

    print("\nGraph 1: Star topology (node 2 is a hub with degree 3, others degree 1)")
    print("          Node degrees: [1, 3, 1, 1]")
    print("\nGraph 2: Linear path (simple chain)")
    print("          Node degrees: [1, 2, 2, 1]")
    print("\nDifference Explanation:")
    print(explain_difference(graph1, graph2))


def example_4_connectivity_mismatch():
    """
    EXPLICIT: Different connectivity structure
    WHY: One graph is fully connected, the other has isolated components
    CONSEQUENCE: Cannot map because one has unreachable nodes
    """
    print_section("EXAMPLE 4: Connectivity Mismatch (Connected vs Disconnected)")

    graph1 = Graph(
        graph_id="test",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="4" lat="3.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
  <way id="2" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="footway" /></way>
  <way id="3" version="1"><nd ref="3" /><nd ref="1" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    graph2 = Graph(
        graph_id="test",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="4" lat="3.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
  <way id="2" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    print(
        "\nGraph 1: Connected (all nodes reachable: 1-2-3-1 forms cycle, node 4 isolated)"
    )
    print("Graph 2: Disconnected (1-2-3 is separate from node 4)")
    print("\nDifference Explanation:")
    print(explain_difference(graph1, graph2))


def example_5_diameter_mismatch():
    """
    EXPLICIT: Different diameters
    WHY: Longest shortest path differs
    CONSEQUENCE: Nodes are at different distances - structural difference
    """
    print_section("EXAMPLE 5: Diameter Mismatch (Longest Shortest Path)")

    graph1 = Graph(
        graph_id="test",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="4" lat="3.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
  <way id="2" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="footway" /></way>
  <way id="3" version="1"><nd ref="3" /><nd ref="4" /><tag k="highway" v="footway" /></way>
  <way id="4" version="1"><nd ref="4" /><nd ref="1" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    graph2 = Graph(
        graph_id="test",
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

    print("\nGraph 1: Circle with 4 nodes (1-2-3-4-1)")
    print("         Diameter = 2 (max distance: node 1 to node 3 is 2 hops)")
    print("\nGraph 2: Linear path with 4 nodes (1-2-3-4)")
    print("         Diameter = 3 (max distance: node 1 to node 4 is 3 hops)")
    print("\nDifference Explanation:")
    print(explain_difference(graph1, graph2))


def example_6_density_mismatch():
    """
    EXPLICIT: Different density
    WHY: One graph is sparse, the other is more densely connected
    CONSEQUENCE: Different connectivity patterns per node
    """
    print_section("EXAMPLE 6: Density Mismatch")

    graph1 = Graph(
        graph_id="test",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
  <way id="2" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="footway" /></way>
  <way id="3" version="1"><nd ref="1" /><nd ref="3" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    graph2 = Graph(
        graph_id="test",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
  <way id="2" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    print("\nGraph 1: Triangle (3 nodes, 3 edges)")
    print("         Density = 1.0 (100% of possible edges present)")
    print("         Edges per node = 1.0")
    print("\nGraph 2: Path (3 nodes, 2 edges)")
    print("         Density = 0.667 (67% of possible edges)")
    print("         Edges per node = 0.667")
    print("\nDifference Explanation:")
    print(explain_difference(graph1, graph2))


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("EXPLICIT ISOMORPHISM FAILURE DESCRIPTIONS")
    print("Detailed, precise explanations of why graphs are not isomorphic")
    print("=" * 80)

    try:
        example_1_node_count_mismatch()
    except Exception as e:
        print(f"Example 1 failed: {e}")

    try:
        example_2_edge_count_mismatch()
    except Exception as e:
        print(f"Example 2 failed: {e}")

    try:
        example_3_degree_sequence_mismatch()
    except Exception as e:
        print(f"Example 3 failed: {e}")

    try:
        example_4_connectivity_mismatch()
    except Exception as e:
        print(f"Example 4 failed: {e}")

    try:
        example_5_diameter_mismatch()
    except Exception as e:
        print(f"Example 5 failed: {e}")

    try:
        example_6_density_mismatch()
    except Exception as e:
        print(f"Example 6 failed: {e}")

    print("\n" + "=" * 80)
    print("All examples completed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
