# Changelog

All notable changes to this project will be documented in this file.

The format is based on * [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

* [New Button] Find feature geometry overlaps
* [New Button] Merge feature geometry overlaps
* [Simplification] Regeneration of fields of features in layers and groups is now a single button
* [Security] User MapsIndoors credentials is now stored the QGIS Password Manager.

## 0.7.21 - 2025-11-28

* [Feature] Visible 3D orientation of model with toggle button
* [Feature] Generate safe dummy graph name without special characaters
* [Optimisation] Improved external id missing messages

## 0.7.20 - 2025-08-01

* [Regression Fix] An import in the "set label field" functionality had become invalid, this is fixed now
* [Feature] Patch english langauge if it is missing or empty now
* [Feature] Auto patch anchors that did end up outside a polygon at upload-time
* [Feature] Location-type based location creation mode button and functionality now controllable through the ADD_LOCATION_TYPE_MODE_TOGGLE flag in settings

## 0.7.19 - 2025-07-30

* [Logic Change] Now reset anchor point on every edit not only when outside geometry

## 0.7.18 - 2025-07-30

* [Bug] In QGIS <3.44.0 the setFieldMergePolicy of QgsVectorLayer is not available, now the download processes do not stop but rather warns the user to upgrade and proceeds

## 0.7.17 - 2025-07-29

* [Simplification] If a translation for a certain language is missing try to migitate from copying en at the moment
* [Feature] Set policy for when splitting, merging and duplicating features.

## 0.7.16 - 2025-07-29

* [Simplification] If a restriction is an empty string then ignore it on location_types, areas and pois as well

## 0.7.15 - 2025-07-29

* [Simplification] If a restriction is an empty string then ignore it

## 0.7.14 - 2025-07-29

* [Bug] Mixed None/NaN/Nat types is now unified to be None/NULL's
* [Bug] Mixed casing categories are now unified as lowercase in lookups
* [Simplification] Collections to Layers is more general now, ensuring that some values are not messed up in serialising and deserialising

## 0.7.13 - 2025-07-26

* [Bug] Anchor generation now uses "point_on_surface" rather than "centroid" to ensure that the anchor point is always inside the polygon

## 0.7.12 - 2025-07-22

* [Bug] If shapely <2.1.0 is already available in QGIS then make sure that equals_exact call is using normalised geometries
* [Feature] 2d_model are now inherited from location_types as well


## 0.7.11 - 2025-07-22

* [Bug] Release pipeline again packaged the wrong Zip of bundles as it failed while resolving

## 0.7.10 - 2025-07-22

* [Bug] Release pipeline packaged the wrong Zip of bundles as it failed while resolving

## 0.7.9 - 2025-07-22

* [Dependency update] OSMNX >= 2.0.0 now supported, allowing a shapely version >=2.1.0

## 0.7.8 - 2025-07-22

* [Optimisation] Only enabled rendering of svg and raster symbol if populated

## 0.7.7 - 2025-07-21

* [Deprecation] Removed AUTO_REGENERATE_EXTERNAL_ID_IF_MISSING functionality
* [Bug-fix] Anchor points of Locations (Room, Area and POI) as well as floor and building are now tracked in
  the attributes tables of features, and is also updated automatically to be centroid if the anchor ends up
  outside the polygon.
* [QOL] Geometry comparison is now tolerance based to avoid reprojection errors producing unnecessary update to
  geometries
* [Validation] All result lon and lat coordinates are now range validation (-90 to 90) and (-180 to 180)
* [Feature] Anchor and 3d-rotation is now visualised in every polygon, can be disabled by setting,
  ADD_ANCHOR_AND_3DROTSCL_SYMBOLS.
* [Feature] Adds support for 2D model styling and visualisation (SVG and raster symbols) on location level, location-type level is still missing

## 0.7.6 - 2025-07-03

* [Deprecation] Removed Compatibility button
* [Feature] Add language to group/layer button
* [Bug-fix] "." is now allowed in admin_id's by the SyncModule
* [Bug-fix] If a field erroneously has a non-lowercase key (Dictated by upload to the ManagerAPI) it is now
  lowered on download.
* [New Button] Added a button "Recalculate 3d Walls" for forcefully recomputing 3D walls aka "DerivedGeometry"
  for solutions based on a solutionId.
* [Bug-fix] Property is_obstacle and is_selectable is now tracked and persisted.
* [QOL] Location-Types dropdown are now sorted by translations.[default-language].name. Duplicate locationtype
  names are grouped together. Admin-id's are displayed when hovered over the locationtype.

## 0.7.5 - 2025-06-04

* [Bug-fix] Solutions with default language other than english is now supported

## 0.7.4 - 2025-06-04

* [Bug-fix] Displayrules of location_types layer now gets parsed

* ## 0.7.1-3 - 2025-06-04

* [Bug-fix] Fixed smaller issue with some data in some solutions

## 0.7.0 - 2025-06-03

* [Workaround] Ignore OSM related issue in the ManagerAPI at the moment.
* [Feature] Details added to locations.
* [Feature] Fields on route-elements are now available.
* [Feature] Multi language solutions now supported. "name" -> "translations.en.name"
* [Feature] Displayrules are now editable through attributes table.
* [Bug-fix] Displayrules with labelSize set now works.
* [Simplification] custom_properties -> fields

## 0.6.11 - 2025-04-08

* [Bug-fix] DisplayString for layer URI is not translated any more, all system locales now supported.
* [Validation] Proactive Layer Hierarchy Validation engine implemented.
* [Validation] Upload time validation of missing layer and geometries.
* [New Button] Toggle off/on labels for all layer.
* [New Button] Bulk Label field expression assignment.
* [New Button] Assign an external id to a solution with 'solution id'.
* [Style Option] Labels on locations can be set to be location_type(s) instead.
* [Optimization] Synchronisation resolving now uses significantly less memory.

## 0.6.10 - 2025-04-01

* [New Layer] LocationType(s) is now an editable layer

## 0.6.9 - 2025-03-25

* [Improvement] Duplication now works on individual layers too, it also copies more of the QGSVectorLayer
  properties now
* [Fix] venue_type dropdown widget now works.

## 0.6.8 - 2025-03-10

* [Improvement] More context-full error messages
* [New Feature] Graph Bounds is now editable
* [Simplification] Solution data layer is now geometry-less to avoid confusion

## 0.6.7 - 2025-03-04

* [Removed] Buttons not relevant to current workflows, for now.

## 0.6.6 - 2025-02-28

* [Maintainance] Suggest removing old unloaded MI Companion bundles message

## 0.6.5 - 2025-02-27

* [New feature] Graph editing support

## 0.6.4 - 2025-02-21

* [Bug-fix] Caddy import now handles 3dfaces in polylines neatly
* [Bug-fix] Venue-type dropdown now has the correct values
* [Usability] Improved default location layer styling, for the upcoming display-rule based styling

## 0.6.4 - 2025-02-21

* [New feature] Compatibility button new displays a report of what was changed

## 0.6.3 - 2025-02-13

* [Visualisation] Graph layer 3d styling
* [New Feature] Support for details on venues, buildings, floors, rooms, pois and areas
* [Data import] IMDF import support

## 0.6.2 - 2025-02-13

* [Validation] Layer geometry constraints now enforced
* [Visualisation] 3D view styling support

## 0.6.0 - 2025-01-14

* [Validation] Validation button added

* [Data import] Import SVG

* [Transform data into QGIS layers] Copy and paste Group with data included

* [Venue Management] Load a Venue
* [Venue Management] Create a Venue
* [Venue Management] Edit a Venue
* [Venue Management] Move a Venue from one Solution to another

* [Building Management] Load a Building
* [Building Management] Create a Building
* [Building Management] Edit a Building
* [Building Management] Move a Building from one Venue to another
* [Building Management] Move a Building from one Solution to another
* [Building Management] Delete a Building

* [Floor Management] Load a Floor
* [Floor Management] Create a Floor
* [Floor Management] Edit a Floor
* [Floor Management] Move a Floor from one Building to another
* [Floor Management] Move a Floor from one Solution to another
* [Floor Management] Delete a Floor

* [Location Management] Load a Location
* [Location Management] Create a Location
* [Location Management] Edit a Location
* [Location Management] Move a Location from one Floor to another
* [Location Management] Move a Location from one Solution to another
* [Location Management] Delete a Location

* [Graph Management] Load a Graph
* [Graph Management] Create a Graph

* [Route Element Management] Load a Route Elements
* [Route Element Management] Create a Route Element
* [Route Element Management] Edit a Route Element
* [Route Element Management] Delete a Route Element

* [Location Type Management] Load a Location Type
* [Location Type Management] Create a Location Type
* [Location Type Management] Edit a Location Type

* [Category Management] Load a Category
* [Category Management] Create a Category
* [Category Management] Edit a Category

* [Transform data into MapsIndoors data] Load data from QGIS layers into MapsIndoors solution

* [Post-processing] Geo-reference a venue
* [Post-processing] Regenerate adminId

* [Upload/Export solution] Upload a solution to MapsIndoors

## 0.5.0 - 2024-12-01

* Project shape to project crs and fix category bug on upload

## 0.4.0 - 2024-11-01

* Address on Venue now supported
* Support for Multi Polygon floors

## 0.3.0 - 2024-10-01

* Handle Custom PROPERties PROPERly, (bug fix)
* More robust hierarchy parsing, and change default target CRS to 3857 and convert back to 4326 on upload
* Graph disabled by default, compatibility entry point

## 0.2.0 - 2024-09-01

* Major parsing refactor, more logging
* Layer Duplication button
* Differentiation of Solutions
* CI Release pipeline

## 0.1.0 - 2024-08-01

* Initial release
