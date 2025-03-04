# Changelog

All notable changes to this project will be documented in this file.

The format is based on * [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
