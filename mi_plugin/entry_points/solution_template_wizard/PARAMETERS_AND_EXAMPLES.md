# Venue Template Wizard - Parameters and Examples

## Overview

The `run()` function generates an empty MapsIndoors solution hierarchy for map creation from scratch. It
creates a complete venue structure with buildings, floors, rooms, areas, points of interest, and connectivity
elements.

---

## Function Parameters

### Required Parameters (Keyword-Only)

#### `solution_external_id: str`

- **Type:** String
- **Description:** The unique external identifier for the MapsIndoors solution. This serves as the primary key
  for identifying the solution in external systems.
- **Example:** `"my_venue_solution_2026"`
- **Notes:** Must be unique across all solutions

#### `solution_customer_id: str`

- **Type:** String
- **Description:** The customer/organization ID that owns this solution. Used to associate the solution with a
  specific customer account.
- **Example:** `"customer_12345"`
- **Notes:** Should match an existing customer ID in your MapsIndoors organization

#### `number_of_floors: int`

- **Type:** Integer
- **Description:** The number of floors to generate in the building. Each floor will have rooms, areas, POIs,
  doors, barriers, and other navigation elements.
- **Example:** `3`
- **Notes:** Must be a positive integer (1 or greater)

### Optional Parameters (Keyword-Only with Defaults)

#### `solution_default_language: str`

- **Type:** String
- **Default:** `SOLUTION_DEFAULT_LANGUAGE` (from module configuration)
- **Description:** The default language code for the solution. Used for all generated translations and language
  bundles.
- **Example:** `"en"` (English), `"da"` (Danish), `"es"` (Spanish)
- **Notes:** Uses ISO 639-1 language codes

#### `solution_available_languages: Tuple[str, ...]`

- **Type:** Tuple of strings
- **Default:** `SOLUTION_DEFAULT_AVAILABLE_LANGUAGES` (from module configuration)
- **Description:** A tuple of all available language codes for this solution. Enables multi-language support.
- **Example:** `("en", "da", "es", "fr")`
- **Notes:** Should include the default language; can be a single-element tuple

---

## Return Value

- **Type:** `None`
- **Side Effects:** Creates and displays a complete venue hierarchy in QGIS with layers representing different
  solution elements

---

## Usage Examples

### Example 1: Basic Single-Language Solution (3 Floors)

```python
from mi_plugin.entry_points.solution_template_wizard import run

run(
    solution_external_id="my_mall_solution",
    solution_customer_id="mall_customer_001",
    number_of_floors=3
    )
```

**Result:** Creates a 3-floor venue with English as the default language

---

### Example 2: Multi-Language Solution (4 Floors)

```python
run(
    solution_external_id="international_mall",
    solution_customer_id="global_customer_456",
    solution_default_language="en",
    solution_available_languages=("en", "da", "es", "fr", "de"),
    number_of_floors=4
    )
```

**Result:** Creates a 4-floor venue with English as default and 4 additional language support

---

### Example 3: Danish Language, Single Floor

```python
run(
    solution_external_id="copenhagen_venue",
    solution_customer_id="danish_org_789",
    solution_default_language="da",
    solution_available_languages=("da",),
    number_of_floors=1
    )
```

**Result:** Creates a single-floor venue with Danish as the only language

---

### Example 4: Large Multi-Floor Complex

```python
run(
    solution_external_id="large_airport_complex",
    solution_customer_id="airport_authority_001",
    solution_default_language="en",
    solution_available_languages=("en", "es", "fr", "zh", "ja", "ar"),
    number_of_floors=8
    )
```

**Result:** Creates an 8-floor venue with 6 language support (typical for international airport)

---

## Generated Structure

For each call to `run()`, the following hierarchy is created:

### Solution Components

1. **Venue** - The overall venue container (1 per solution)
2. **Graph** - Navigation graph for routing and pathfinding (1 per solution)
3. **Building** - Physical building structure (1 per solution)

### Per Floor (repeated for each floor):

- **Floor** - Floor definition with index
- **Rooms** - At least one room per floor
- **Areas** - At least one area per floor
- **Points of Interest (POIs)** - At least one POI per floor with occupant

### Global Elements

- **Location Type** - Entity type for POIs
- **Category** - Classification for POIs
- **Occupant Category** - Classification for occupant types
- **Occupant Template** - Template for occupants
- **Media** - Sample media asset (PNG image)
- **Navigation Elements per Floor:**
    - Doors
    - Barriers
    - Preferences (preferred routes)
    - Avoidance zones
    - Entry points
    - Obstacles

### Connectivity

- **Elevator Connection** - Connects multiple floors with vertical transportation

---

## Data Details

### Generated IDs

- **Solution ID:** Uses the provided `solution_external_id`
- **Entity IDs:** All generated entities use the `"dummy"` prefix
    - Example: `"dummy"`, `"dummy0"`, `"dummy1"`, etc.

### Geometric Data

- **Venue Polygon:** 1 unit radius circle centered at (0, 0)
- **Building Polygon:** Same as venue
- **Floor Polygons:** Same as venue/building
- **Room/Area Polygons:** Same as venue/building/floor
- **POI Points:** (0, 0)
- **Graph Network:** Simple LineString from (0, 0) to (0, 1)

### Navigation Elements

- **Doors:** One per floor, positioned at (0, 0)
- **Barriers:** One per floor, positioned at (0, 0)
- **Preferences:** One per floor, positioned at (0, 0)
- **Avoidance Zones:** One per floor, positioned at (0, 0)
- **Entry Points:** One per floor, positioned at (0, 0)
- **Obstacles:** One per floor, 0.5 unit radius circle at (0, 0)

### Elevator Connection

- **Start Node:** Floor 0, position (0, 0)
- **End Node:** Floor 1, position (0, 0)
- **Type:** Elevator (vertical transportation)

---

## QGIS Integration

The function integrates with QGIS by:

1. **Creating Layers:** All solution components are added as layers to the QGIS layer tree
2. **Organizing Hierarchy:** Layers are organized under group nodes following the MapsIndoors hierarchy
3. **Clearing Existing Data:** Non-solution layers are emptied of features (but structure is preserved)
4. **Visual Feedback:** Progress bar indicates creation progress

---

## Common Use Cases

### Use Case 1: Creating a Test Venue

```python
# Quick test with minimal floors
run(
    solution_external_id="test_venue",
    solution_customer_id="test_customer",
    number_of_floors=1
    )
```

### Use Case 2: Building a Real Venue

```python
# Detailed venue for actual mapping project
run(
    solution_external_id="corporate_headquarters",
    solution_customer_id="fortune_500_corp",
    solution_default_language="en",
    solution_available_languages=("en", "es", "fr"),
    number_of_floors=15
    )
```

### Use Case 3: Regional Multi-Language Venue

```python
# Venue supporting regional languages
run(
    solution_external_id="european_shopping_center",
    solution_customer_id="retail_group_eu",
    solution_default_language="en",
    solution_available_languages=("en", "de", "fr", "it", "nl", "pl"),
    number_of_floors=4
    )
```

---

## Error Handling

The function performs the following operations:

1. Instantiates a QGIS project instance
2. Creates geometric shapes (points, lines, polygons)
3. Adds solution layers to the layer tree
4. Clears features from non-solution groups

**Note:** The function currently uses try/except in dialogs but may raise exceptions if:

- QGIS instance is not available
- Customer ID is invalid
- Language codes are not recognized
- Geometric operations fail

---

## Notes

- The generated solution contains dummy data for testing and template purposes
- All translations use the specified `solution_default_language`
- The template is designed to be quickly customized for actual venue data
- The function is keyword-only (must use parameter names)
- Progress feedback is provided via QGIS status bar
