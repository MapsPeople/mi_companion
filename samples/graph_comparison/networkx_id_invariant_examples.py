"""
Example: Node ID and Edge ID Invariant Graph Comparison

Demonstrates that graph comparison is now INVARIANT to node and edge ID differences.
Two graphs with different node/edge IDs are considered equal if they have the same structure.

This uses networkx graph relabeling for clean, efficient comparison.
"""

from sync_module.model.graph import Graph


def example_1_different_node_ids():
    """
    Graph 1: Nodes with IDs [1, 2, 3] forming a path 1-2-3
    Graph 2: Nodes with IDs [100, 200, 300] forming the same path

    Result: EQUAL (same structure, different node IDs)
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Different Node IDs (Same Structure)")
    print("=" * 80)

    graph1 = Graph(
        graph_id="path_graph",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
  <way id="2" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    graph2 = Graph(
        graph_id="path_graph",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="100" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="200" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="300" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="10" version="1"><nd ref="100" /><nd ref="200" /><tag k="highway" v="footway" /></way>
  <way id="20" version="1"><nd ref="200" /><nd ref="300" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    result = graph1 == graph2
    print(f"\nGraph 1 nodes: [1, 2, 3]")
    print(f"Graph 2 nodes: [100, 200, 300]")
    print(f"\nGraphs equal: {result}")
    print(f"Expected: True (same structure, different node IDs)")
    print(f"Status: {'✅ PASS' if result else '❌ FAIL'}")


def example_2_different_edge_ids():
    """
    Graph 1: Edges with IDs [1, 2, 3]
    Graph 2: Edges with IDs [500, 600, 700]

    Result: EQUAL (same structure, different edge IDs)
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Different Edge IDs (Same Structure)")
    print("=" * 80)

    graph1 = Graph(
        graph_id="triangle",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
  <way id="2" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="footway" /></way>
  <way id="3" version="1"><nd ref="3" /><nd ref="1" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    graph2 = Graph(
        graph_id="triangle",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="500" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
  <way id="600" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="footway" /></way>
  <way id="700" version="1"><nd ref="3" /><nd ref="1" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    result = graph1 == graph2
    print(f"\nGraph 1 edges: [1, 2, 3]")
    print(f"Graph 2 edges: [500, 600, 700]")
    print(f"\nGraphs equal: {result}")
    print(f"Expected: True (same structure, different edge IDs)")
    print(f"Status: {'✅ PASS' if result else '❌ FAIL'}")


def example_3_different_node_and_edge_ids():
    """
    Graph 1: Nodes [1,2,3,4], Edges [1,2,3]
    Graph 2: Nodes [50,60,70,80], Edges [500,600,700]

    Result: EQUAL (same structure, completely different IDs)
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Different Node AND Edge IDs (Same Structure)")
    print("=" * 80)

    graph1 = Graph(
        graph_id="star",
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
        graph_id="star",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="50" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="60" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="70" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="80" lat="3.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="500" version="1"><nd ref="60" /><nd ref="50" /><tag k="highway" v="footway" /></way>
  <way id="600" version="1"><nd ref="60" /><nd ref="70" /><tag k="highway" v="footway" /></way>
  <way id="700" version="1"><nd ref="60" /><nd ref="80" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    result = graph1 == graph2
    print(f"\nGraph 1 nodes: [1,2,3,4], edges: [1,2,3] (star topology)")
    print(f"Graph 2 nodes: [50,60,70,80], edges: [500,600,700] (star topology)")
    print(f"\nGraphs equal: {result}")
    print(f"Expected: True (same structure, completely different IDs)")
    print(f"Status: {'✅ PASS' if result else '❌ FAIL'}")


def example_4_different_structure():
    """
    Graph 1: Linear path (1-2-3)
    Graph 2: Different structure (triangle)

    Result: NOT EQUAL (different structure, different IDs)
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Different Structures (NOT Equal)")
    print("=" * 80)

    graph1 = Graph(
        graph_id="path",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
  <way id="2" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    graph2 = Graph(
        graph_id="path",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="100" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="200" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="300" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="500" version="1"><nd ref="100" /><nd ref="200" /><tag k="highway" v="footway" /></way>
  <way id="600" version="1"><nd ref="200" /><nd ref="300" /><tag k="highway" v="footway" /></way>
  <way id="700" version="1"><nd ref="300" /><nd ref="100" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    result = graph1 == graph2
    print(f"\nGraph 1: Linear path (3 nodes, 2 edges)")
    print(f"Graph 2: Triangle (3 nodes, 3 edges)")
    print(f"\nGraphs equal: {result}")
    print(f"Expected: False (different structures)")
    print(f"Status: {'✅ PASS' if not result else '❌ FAIL'}")


def example_5_networkx_relabeling_demo():
    """
    Demonstrate the networkx relabeling mechanism directly
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 5: NetworkX Graph Relabeling Mechanism")
    print("=" * 80)

    graph1 = Graph(
        graph_id="demo",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="alice" lat="0.0" lon="0.0" version="1"><tag k="name" v="Alice" /></node>
  <node id="bob" lat="1.0" lon="0.0" version="1"><tag k="name" v="Bob" /></node>
  <node id="charlie" lat="2.0" lon="0.0" version="1"><tag k="name" v="Charlie" /></node>
  <way id="edge1" version="1"><nd ref="alice" /><nd ref="bob" /><tag k="type" v="friendship" /></way>
  <way id="edge2" version="1"><nd ref="bob" /><nd ref="charlie" /><tag k="type" v="friendship" /></way>
</osm>""",
    )

    graph2 = Graph(
        graph_id="demo",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="name" v="Person1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="name" v="Person2" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="name" v="Person3" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="type" v="friendship" /></way>
  <way id="2" version="1"><nd ref="2" /><nd ref="3" /><tag k="type" v="friendship" /></way>
</osm>""",
    )

    result = graph1 == graph2
    print(f"\nGraph 1 nodes: [alice, bob, charlie] (named IDs)")
    print(f"Graph 2 nodes: [1, 2, 3] (numeric IDs)")
    print(f"\nBoth form the same linear connectivity pattern")
    print(f"\nGraphs equal: {result}")
    print(f"Expected: True (normalized by networkx relabeling)")
    print(f"Status: {'✅ PASS' if result else '❌ FAIL'}")

    print("\nHow it works:")
    print("1. Convert OSM XML to networkx graph (nodes: alice, bob, charlie)")
    print("2. Normalize node IDs using nx.relabel_nodes() (alice→1, bob→2, charlie→3)")
    print("3. Compare isomorphism between normalized graphs")
    print("4. Result: Graphs are equal because structure is identical")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("NODE AND EDGE ID INVARIANT GRAPH COMPARISON")
    print("Using NetworkX Graph Relabeling")
    print("=" * 80)

    try:
        example_1_different_node_ids()
    except Exception as e:
        print(f"Example 1 failed: {e}")

    try:
        example_2_different_edge_ids()
    except Exception as e:
        print(f"Example 2 failed: {e}")

    try:
        example_3_different_node_and_edge_ids()
    except Exception as e:
        print(f"Example 3 failed: {e}")

    try:
        example_4_different_structure()
    except Exception as e:
        print(f"Example 4 failed: {e}")

    try:
        example_5_networkx_relabeling_demo()
    except Exception as e:
        print(f"Example 5 failed: {e}")

    print("\n" + "=" * 80)
    print("All examples completed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
