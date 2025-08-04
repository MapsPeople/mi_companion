#!/usr/bin/python
import logging
from pathlib import Path

import ifcopenshell # pip install ifcopenshell trimesh
import trimesh
import json
import os
import sys
from pathlib import Path
# noinspection PyUnresolvedReferences
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject

# noinspection PyUnresolvedReferences
from qgis.utils import iface

import ifcopenshell.geom
import numpy as np
from scipy.spatial.transform import Rotation
import json
from typing import List, Dict, Tuple, Callable, Optional, Any, Union
from jord.qgis_utilities.helpers import InjectedProgressBar
from mi_companion import RESOURCE_BASE_PATH
from mi_companion.layer_descriptors import DATABASE_GROUP_DESCRIPTOR
from mi_companion.mi_editor.conversion import add_solution_layers

logger = logging.getLogger(RESOURCE_BASE_PATH)
__all__ = ["run"]


def load_ifc(file_path: Path) -> ifcopenshell.entity_instance:
    return ifcopenshell.open(file_path)

def iuh():
  # !/usr/bin/env python3
  # This Source Code Form is subject to the terms of the Mozilla Public
  # License, v. 2.0. If a copy of the MPL was not distributed with this
  # file, You can obtain one at https://mozilla.org/MPL/2.0/.
  #
  # Project:     ifc2geojson [IFC (BIM) to GeoJSON (GIS) converter]



  class GeoJsonExporter:

    def __init__(self):
      self.transform_callback = lambda p: [p[0], p[1], p[2]]
      self.projection = "EPSG:3857"
      self.precision = 8

    def set_projection(self, projection: str):
      self.projection = projection
      return self

    def set_precision(self, precision: int):
      self.precision = precision
      return self

    def set_transform_callback(self, fn: Callable):
      if callable(fn):
        self.transform_callback = fn
      return self

    def parse(self, meshes: List[Dict]) -> Dict:
      if not meshes:
        return None

      def to_coords(v: np.ndarray) -> List[float]:
        x, y, z = self.transform_callback(v)
        return [
            float(round(x, self.precision)),
            float(round(y, self.precision)),
            float(round(z, self.precision))
            ]

      features = []

      for mesh in meshes:
        vertices = mesh["vertices"]
        faces = mesh["faces"]
        properties = mesh.get("properties", {})

        polygons = []
        for face in faces:
          va = to_coords(vertices[face[0]])
          vb = to_coords(vertices[face[1]])
          vc = to_coords(vertices[face[2]])
          polygons.append([va, vb, vc, va])  # Close the polygon

        if len(polygons) > 1:
          geometry = {
              "type": "MultiPolygon",
              "coordinates": [[polygon] for polygon in polygons]
              }
        else:
          geometry = {
              "type": "Polygon",
              "coordinates": [polygons[0]]
              }

        feature = {
            "type": "Feature",
            "properties": properties,
            "geometry": geometry
            }
        features.append(feature)

      if not features:
        return None

      return {
          "type": "FeatureCollection",
          "features": features
          }

  SI_PREFIXES = {
      "EXA": 1e18, "PETA": 1e15, "TERA": 1e12, "GIGA": 1e9, "MEGA": 1e6,
      "KILO": 1e3, "HECTO": 1e2, "DECA": 1e1, "DECI": 1e-1, "CENTI": 1e-2,
      "MILLI": 1e-3, "MICRO": 1e-6, "NANO": 1e-9
      }

  LENGTH_UNITS = {
      "METRE": 1,
      "FOOT": 0.3048,
      "INCH": 0.0254
      }

  def get_unit_scale(model) -> float:
    try:
      project = model.by_type("IfcProject")[0]
      units = project.UnitsInContext.Units

      for unit in units:
        if unit.is_a("IfcSIUnit") and unit.UnitType == "LENGTHUNIT":
          base_name = unit.Name or "METRE"
          base = LENGTH_UNITS.get(base_name, 1)
          prefix_name = unit.Prefix
          factor = SI_PREFIXES.get(prefix_name, 1) if prefix_name else 1
          return base * factor

    except Exception as err:
      print(f"⚠️ Failed to detect unit scale. Defaulting to 1 (meters). {err}")
      return 1

    print("⚠️ No LENGTHUNIT found. Defaulting to 1 (meters).")
    return 1

  def get_ifc_map_conversion_matrix(model) -> np.ndarray:
    map_conv = None
    try:
      map_convs = model.by_type("IfcMapConversion")
      if map_convs:
        map_conv = map_convs[0]
    except:
      pass

    if not map_conv:
      return np.identity(4)

    eastings = getattr(map_conv, "Eastings", 0) or 0
    northings = getattr(map_conv, "Northings", 0) or 0
    ortho_height = getattr(map_conv, "OrthogonalHeight", 0) or 0

    x_axis_x = getattr(map_conv, "XAxisAbscissa", 1) or 1
    x_axis_y = getattr(map_conv, "XAxisOrdinate", 0) or 0
    scale = getattr(map_conv, "Scale", 1) or 1

    # Normalize x axis vector
    x_axis_length = np.sqrt(x_axis_x ** 2 + x_axis_y ** 2)
    x_axis = np.array([x_axis_x / x_axis_length, x_axis_y / x_axis_length, 0])
    z_axis = np.array([0, 0, 1])
    y_axis = np.cross(z_axis, x_axis)

    # Get unit scale
    unit_scale = get_unit_scale(model)

    # Create transformation matrix
    rotation_matrix = np.column_stack([x_axis, y_axis, z_axis])
    translation = np.array([eastings * unit_scale, northings * unit_scale, ortho_height * unit_scale])

    matrix = np.identity(4)
    matrix[:3, :3] = rotation_matrix * scale
    matrix[:3, 3] = translation

    return matrix

  def ifc2geojson(
      ifc_data: bytes, crs: str = "urn:ogc:def:crs:EPSG::3857",
      msg_callback: Callable = lambda msg: None
      ) -> Dict:
    # Load IFC model
    model = ifcopenshell.file.from_string(
      ifc_data.decode('utf-8')
      if isinstance(ifc_data, bytes) else ifc_data
      )

    msg_callback("Loading geometries...")
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)

    # Get map conversion matrix
    map_matrix = get_ifc_map_conversion_matrix(model)

    # Flip Y <-> Z (in GIS, Z is up)
    flip_matrix = np.array(
        [
            [1, 0, 0, 0],
            [0, 0, -1, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1]
            ]
        )

    final_matrix = np.matmul(map_matrix, flip_matrix)

    # Process all products with geometry
    meshes = []
    for product in model.by_type("IfcProduct"):
      if not product.Representation:
        continue

      try:
        shape = ifcopenshell.geom.create_shape(settings, product)
        vertices = np.array(shape.geometry.verts).reshape(-1, 3)
        faces = np.array(shape.geometry.faces).reshape(-1, 3)

        # Apply transformation matrix to vertices
        homogeneous_vertices = np.ones((vertices.shape[0], 4))
        homogeneous_vertices[:, :3] = vertices
        transformed_vertices = np.matmul(homogeneous_vertices, final_matrix.T)[:, :3]

        properties = {}
        for prop in product.IsDefinedBy:
          if hasattr(prop, "RelatingPropertyDefinition"):
            pdef = prop.RelatingPropertyDefinition
            if hasattr(pdef, "HasProperties"):
              for p in pdef.HasProperties:
                if hasattr(p, "Name") and hasattr(p, "NominalValue"):
                  if p.NominalValue:
                    properties[p.Name] = p.NominalValue.wrappedValue

        # Add GlobalId
        properties["GlobalId"] = product.GlobalId

        meshes.append(
            {
                "vertices": transformed_vertices,
                "faces": faces,
                "properties": properties
                }
            )

      except Exception as e:
        print(f"Error processing {product.is_a()}: {e}")
        continue

    msg_callback("Converting to GeoJSON...")
    exporter = GeoJsonExporter()
    geojson = exporter.parse(meshes)

    geojson_with_crs = {
        **geojson,
        "crs": {
            "type": "name",
            "properties": {
                "name": crs
                }
            }
        }

    return geojson_with_crs

  def ifc2geojson_blob(
      ifc_data: bytes, crs: str = "urn:ogc:def:crs:EPSG::3857",
      msg_callback: Callable = lambda msg: None
      ) -> bytes:
    geojson_with_crs = ifc2geojson(ifc_data, crs, msg_callback)
    json_string = json.dumps(geojson_with_crs)
    return json_string.encode('utf-8')

  def get_geopackage_properties_from_geojson(geojson: Dict) -> List[Dict]:
    type_map = {
        "str": "TEXT",
        "int": "INTEGER",
        "float": "REAL",
        "bool": "BOOLEAN",
        }

    seen_props = {}

    for feature in geojson.get("features", []):
      props = feature.get("properties", {})
      for key, value in props.items():
        if key not in seen_props:
          js_type = type(value).__name__
          data_type = type_map.get(js_type, "TEXT")  # default fallback
          seen_props[key] = data_type

    tab_properties = [{"name": name, "dataType": data_type}
                      for name, data_type in seen_props.items()]

    return tab_properties




  def print_message(msg):
    """Simple callback function to display progress messages"""
    print(f"Status: {msg}")

  def convert_ifc_file(ifc_file_path, output_file_path=None):
    """Convert an IFC file to GeoJSON and save the result"""
    try:
      # Read the IFC file as bytes
      with open(ifc_file_path, 'rb') as f:
        ifc_data = f.read()

      # Convert to GeoJSON
      geojson_result = ifc2geojson(
          ifc_data,
          crs="urn:ogc:def:crs:EPSG::4326",  # WGS 84 - standard geographic coordinates
          msg_callback=print_message
          )

      # Determine output path
      if output_file_path is None:
        output_file_path = Path(ifc_file_path).with_suffix('.geojson')

      # Save the result
      with open(output_file_path, 'w') as f:
        import json

        json.dump(geojson_result, f, indent=2)

      print(f"Successfully converted {ifc_file_path} to {output_file_path}")

      # Alternative: get the result as bytes
      # geojson_bytes = ifc2geojson_blob(ifc_data, msg_callback=print_message)
      # with open(output_file_path, 'wb') as f:
      #     f.write(geojson_bytes)

      return True

    except Exception as e:
      print(f"Error converting IFC file: {e}")
      return False

  def asd():
    # Example usage from command line
    if len(sys.argv) < 2:
      print("Usage: python script.py <ifc_file_path> [output_file_path]")
      sys.exit(1)

    ifc_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    if not os.path.exists(ifc_path):
      print(f"Error: File not found: {ifc_path}")
      sys.exit(1)

    success = convert_ifc_file(ifc_path, output_path)
    sys.exit(0 if success else 1)

  asd()

def ifc_to_mi_solution(ifc_model):
    """


    :param ifc_model:
    :return:
    """



    def ifc_to_geojson(ifc_path):
      # Load IFC model
      model = ifcopenshell.open(ifc_path)
      features = []

      # Iterate over all products with geometry
      for product in model.by_type("IfcProduct"):
        if not hasattr(product, "Representation") or not product.Representation:
          continue
        try:
          shape = ifcopenshell.geom.create_shape({'instance': product})
          mesh = trimesh.Trimesh(
            vertices=shape.geometry.verts.reshape(-1, 3),
            faces=shape.geometry.faces.reshape(-1, 3)
            )
          for face in mesh.faces:
            coords = [mesh.vertices[idx].tolist() for idx in face] + [mesh.vertices[face[0]].tolist()]
            feature = {
                "type": "Feature",
                "properties": {"GlobalId": product.GlobalId},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [coords]
                    }
                }
            features.append(feature)
        except Exception:
          continue

      geojson = {
          "type": "FeatureCollection",
          "features": features
          }
      return geojson

    # Example usage
    ifc_file = "example.ifc"
    geojson = ifc_to_geojson(ifc_file)
    with open("output.geojson", "w") as f:
      json.dump(geojson, f)

    return None


def run(*, ifc_zip_file_path: Path) -> None:
    """
    Does nothing yet.

    :param ifc_zip_file_path:
    :return:
    """
    qgis_instance_handle = QgsProject.instance()
    layer_tree_root = QgsProject.instance().layerTreeRoot()

    ifc_model = load_ifc(ifc_zip_file_path)

    mi_solution = ifc_to_mi_solution(ifc_model)

    with InjectedProgressBar(parent=iface.mainWindow().statusBar()) as progress_bar:
        add_solution_layers(
            qgis_instance_handle=qgis_instance_handle,
            solution=mi_solution,
            layer_tree_root=layer_tree_root,
            mi_hierarchy_group_name=DATABASE_GROUP_DESCRIPTOR,
            progress_bar=progress_bar,
        )
