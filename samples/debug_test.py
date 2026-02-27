"""Debug script to identify test failure."""

import sys

sys.path.insert(0, "..")

from sync_module.constants import FALLBACK_OSM_GRAPH
from sync_module.tools.graph_utilities import (
    osm_xml_to_network,
    osm_xml_to_lines,
    lines_3d_to_osm_xml,
    graphs_are_isomorphic,
)

print("=" * 80)
print("TESTING GRAPH CONVERSION AND ISOMORPHISM")
print("=" * 80)

# Step 1: Create initial graph from OSM XML
print("\n1. Converting OSM XML to network graph...")
g1 = osm_xml_to_network(FALLBACK_OSM_GRAPH)
print(f"   ✓ g1: {g1.number_of_nodes()} nodes, {g1.number_of_edges()} edges")
print(f"   Type: {type(g1)}")

# Step 2: Convert to lines
print("\n2. Converting OSM XML to lines...")
lines, attrs = osm_xml_to_lines(FALLBACK_OSM_GRAPH)
print(f"   ✓ lines: {len(lines)} lines")
print(f"   ✓ attrs: {len(attrs)} attributes")

# Step 3: Convert lines back to OSM XML
print("\n3. Converting lines back to OSM XML...")
d = lines_3d_to_osm_xml(zip(*lines))
print(f"   ✓ OSM XML: {len(d)} bytes")

# Step 4: Create new graph from converted OSM XML
print("\n4. Converting converted OSM XML back to network graph...")
g2 = osm_xml_to_network(d.decode("utf-8"))
print(f"   ✓ g2: {g2.number_of_nodes()} nodes, {g2.number_of_edges()} edges")
print(f"   Type: {type(g2)}")

# Step 5: Compare basic structure
print("\n5. Comparing basic structure...")
print(f"   Order match: {g1.order() == g2.order()}")
print(f"   Size match: {g1.size() == g2.size()}")

# Step 6: Inspect first node
print("\n6. Inspecting node attributes...")
if g1.number_of_nodes() > 0 and g2.number_of_nodes() > 0:
    n1 = list(g1.nodes())[0]
    n2 = list(g2.nodes())[0]
    print(f"   g1 node {n1}: {g1.nodes[n1]}")
    print(f"   g2 node {n2}: {g2.nodes[n2]}")

# Step 7: Inspect first edge
print("\n7. Inspecting edge attributes...")
if g1.number_of_edges() > 0 and g2.number_of_edges() > 0:
    if isinstance(g1, (type(None).__bases__[0])):  # MultiGraph check
        e1 = list(g1.edges(keys=True))[0]
        e2 = list(g2.edges(keys=True))[0]
        print(f"   g1 edge {e1[:2]}: {g1.edges[e1[0], e1[1], e1[2]]}")
        print(f"   g2 edge {e2[:2]}: {g2.edges[e2[0], e2[1], e2[2]]}")
    else:
        e1 = list(g1.edges())[0]
        e2 = list(g2.edges())[0]
        print(f"   g1 edge {e1}: {g1.edges[e1]}")
        print(f"   g2 edge {e2}: {g2.edges[e2]}")

# Step 8: Test isomorphism
print("\n8. Testing isomorphism...")
try:
    result = graphs_are_isomorphic(g1, g2)
    print(f"   Result: {result}")
    if result:
        print("   ✓ PASS: Graphs are isomorphic!")
    else:
        print("   ✗ FAIL: Graphs are NOT isomorphic!")
except Exception as e:
    print(f"   ✗ ERROR: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 80)
