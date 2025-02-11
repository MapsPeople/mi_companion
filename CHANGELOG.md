# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## Unreleased

* Nothing

## 0.6.0 - 2025-01-14

* Added a validation button

* Data import:
    * Import SVG

* Transform data into QGIS layers:
    * Copy and paste Group with data included

* Venue Management:
    * Load a Venue
    * Create a Venue
    * Edit Venue
    * Move Venue from one Solution to another

* Building Management:
    * Load a Building
    * Create a Building
    * Edit Building
    * Move Building from one Venue to another
    * Move Building from one Solution to another
    * Delete Building

* Floor Management:
    * Load a Floor
    * Create a Floor
    * Edit Floor
    * Move Floor from one Building to another
    * Move Floor from one Solution to another
    * Delete Floor

* Location Management:
    * Load a Location
    * Create a Location
    * Edit Location
    * Move Location from one Floor to another
    * Move Location from one Solution to another
    * Delete Location

* Graph Management:
    * Load a Graph
    * Create a Graph

* Route Element Management:
    * Load Route Elements
    * Create a Route Element
    * Edit Route Element
    * Delete Route Element

* Location Type Management:
    * Load a Location Type
    * Create a Location Type
    * Edit Location Type

* Category Management:
    * Load a Category
    * Create a Category
    * Edit Category

* Transform data into MapsIndoors data:
    * Load data from QGIS layer into MapsIndoors solution

* Post processing:
    * Geo-reference a venue
    * Regenerate adminId

* Upload/Export solution:
    * Upload solution to MapsIndoors
    * Automated dependency lookups of QGIS plugin for Windows

## 0.5.0 - 2024-12-01

* Project shape to project crs and fix category bug on upload

## 0.4.0 - 2024-11-01

* Address on Venue now supported
* Support for Multi Polygon floors

## 0.3.0 - 2024-10-01

* Handle Custom PROPERties PROPERly
* More robust hierarchy parsing, and change default target CRS to 3857 and convert back to 4326 on upload
* Graph disabled, compat entry point and square new solution default polygons

## 0.2.0 - 2024-09-01

* Major parsing refactor, more logging
* Tested and ready for use
* Layer Duplication
* Svg import
* Manager API
* Differentiation
* CI Release

## 0.1.0 - 2024-08-01

* Initial release
