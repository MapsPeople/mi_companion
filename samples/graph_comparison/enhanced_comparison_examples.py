"""
Example: Enhanced Graph Comparison with Coordinates and Attributes

Demonstrates comparison considering:
1. Graph structure (nodes, edges)
2. Node coordinates (lat, lon)
3. Node attributes
4. Edge attributes

Two graphs are equal ONLY if all these aspects match.
"""

from sync_module.model.graph import Graph


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def example_1_same_structure_different_coords():
    """
    Graph 1: Nodes at (0,0), (1,0), (2,0)
    Graph 2: Nodes at (0,0), (1,0), (5,0) - different third node location

    Result: NOT EQUAL (same structure, different coordinates)
    """
    print_section("EXAMPLE 1: Same Structure, Different Coordinates")

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
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="3" lat="5.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
  <way id="2" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    result = graph1 == graph2
    print(f"\nGraph 1: Nodes at (0,0), (1,0), (2,0)")
    print(f"Graph 2: Nodes at (0,0), (1,0), (5,0)")
    print(f"\nStructure: Same (path topology)")
    print(f"Coordinates: Different (node 3)")
    print(f"\nGraphs equal: {result}")
    print(f"Expected: False (coordinates differ)")
    print(f"Status: {'✅ PASS' if not result else '❌ FAIL'}")


def example_2_same_structure_coords_different_attributes():
    """
    Graph 1: Nodes with attribute level="1"
    Graph 2: Nodes with attribute level="2"

    Result: NOT EQUAL (same structure + coords, different attributes)
    """
    print_section("EXAMPLE 2: Same Structure and Coords, Different Node Attributes")

    graph1 = Graph(
        graph_id="path",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /><tag k="name" v="start" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /><tag k="name" v="middle" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /><tag k="name" v="end" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
  <way id="2" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    graph2 = Graph(
        graph_id="path",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="2" /><tag k="name" v="start" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="2" /><tag k="name" v="middle" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="level" v="2" /><tag k="name" v="end" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
  <way id="2" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    result = graph1 == graph2
    print(f"\nGraph 1: All nodes level='1'")
    print(f"Graph 2: All nodes level='2'")
    print(f"\nStructure: Same (path topology)")
    print(f"Coordinates: Same")
    print(f"Node Attributes: Different (level tag)")
    print(f"\nGraphs equal: {result}")
    print(f"Expected: False (attributes differ)")
    print(f"Status: {'✅ PASS' if not result else '❌ FAIL'}")


def example_3_same_everything():
    """
    Graph 1 and Graph 2: Identical everything

    Result: EQUAL (same structure, coords, and attributes)
    """
    print_section("EXAMPLE 3: Identical Structure, Coords, and Attributes")

    graph1 = Graph(
        graph_id="path",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /><tag k="name" v="A" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /><tag k="name" v="B" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /><tag k="name" v="C" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
  <way id="2" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    graph2 = Graph(
        graph_id="path",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="10" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /><tag k="name" v="A" /></node>
  <node id="20" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /><tag k="name" v="B" /></node>
  <node id="30" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /><tag k="name" v="C" /></node>
  <way id="100" version="1"><nd ref="10" /><nd ref="20" /><tag k="highway" v="footway" /></way>
  <way id="200" version="1"><nd ref="20" /><nd ref="30" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    result = graph1 == graph2
    print(f"\nGraph 1: nodes [1,2,3], ways [1,2]")
    print(f"Graph 2: nodes [10,20,30], ways [100,200]")
    print(f"\nStructure: Same (path topology)")
    print(f"Coordinates: Same (0,0), (1,0), (2,0)")
    print(f"Attributes: Same (level=1, names A,B,C)")
    print(f"\nGraphs equal: {result}")
    print(f"Expected: True (everything identical)")
    print(f"Status: {'✅ PASS' if result else '❌ FAIL'}")


def example_4_different_edge_attributes():
    """
    Graph 1: Ways with highway="footway"
    Graph 2: Ways with highway="cycleway"

    Result: NOT EQUAL (same structure + coords, different edge attributes)
    """
    print_section("EXAMPLE 4: Same Structure and Coords, Different Edge Attributes")

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
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="3" lat="2.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="cycleway" /></way>
  <way id="2" version="1"><nd ref="2" /><nd ref="3" /><tag k="highway" v="cycleway" /></way>
</osm>""",
    )

    result = graph1 == graph2
    print(f"\nGraph 1: Ways with highway='footway'")
    print(f"Graph 2: Ways with highway='cycleway'")
    print(f"\nStructure: Same (path topology)")
    print(f"Coordinates: Same")
    print(f"Node Attributes: Same")
    print(f"Edge Attributes: Different (highway type)")
    print(f"\nGraphs equal: {result}")
    print(f"Expected: False (edge attributes differ)")
    print(f"Status: {'✅ PASS' if not result else '❌ FAIL'}")


def example_5_tolerance_in_coordinates():
    """
    Graph 1: Node at (0.0, 0.0)
    Graph 2: Node at (0.0000001, 0.0) - within floating point tolerance

    Result: EQUAL (coordinates within tolerance)
    """
    print_section("EXAMPLE 5: Coordinate Tolerance (Floating Point Precision)")

    graph1 = Graph(
        graph_id="simple",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    graph2 = Graph(
        graph_id="simple",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0000001" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    result = graph1 == graph2
    print(f"\nGraph 1: Node 1 at (0.0, 0.0)")
    print(f"Graph 2: Node 1 at (0.0000001, 0.0)")
    print(f"\nDifference: 1e-7 (within tolerance of 1e-6)")
    print(f"\nGraphs equal: {result}")
    print(f"Expected: True (within floating point tolerance)")
    print(f"Status: {'✅ PASS' if result else '❌ FAIL'}")


def example_6_missing_attributes():
    """
    Graph 1: Nodes with attribute level="1"
    Graph 2: Nodes without level attribute

    Result: NOT EQUAL (different attributes)
    """
    print_section("EXAMPLE 6: Missing Attributes")

    graph1 = Graph(
        graph_id="path",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <node id="2" lat="1.0" lon="0.0" version="1"><tag k="level" v="1" /></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    graph2 = Graph(
        graph_id="path",
        osm_xml="""<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="0.0" lon="0.0" version="1"></node>
  <node id="2" lat="1.0" lon="0.0" version="1"></node>
  <way id="1" version="1"><nd ref="1" /><nd ref="2" /><tag k="highway" v="footway" /></way>
</osm>""",
    )

    result = graph1 == graph2
    print(f"\nGraph 1: Nodes with level='1' attribute")
    print(f"Graph 2: Nodes without attributes")
    print(f"\nGraphs equal: {result}")
    print(f"Expected: False (different attributes)")
    print(f"Status: {'✅ PASS' if not result else '❌ FAIL'}")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("ENHANCED GRAPH COMPARISON")
    print("Considering Structure, Coordinates, and Attributes")
    print("=" * 80)

    try:
        example_1_same_structure_different_coords()
    except Exception as e:
        print(f"Example 1 failed: {e}")

    try:
        example_2_same_structure_coords_different_attributes()
    except Exception as e:
        print(f"Example 2 failed: {e}")

    try:
        example_3_same_everything()
    except Exception as e:
        print(f"Example 3 failed: {e}")

    try:
        example_4_different_edge_attributes()
    except Exception as e:
        print(f"Example 4 failed: {e}")

    try:
        example_5_tolerance_in_coordinates()
    except Exception as e:
        print(f"Example 5 failed: {e}")

    try:
        example_6_missing_attributes()
    except Exception as e:
        print(f"Example 6 failed: {e}")

    print("\n" + "=" * 80)
    print("All examples completed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
