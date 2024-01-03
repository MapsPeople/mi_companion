#!/usr/bin/python


import csv
import os
import traceback
from pathlib import Path
from typing import List, Optional, Sequence, Dict, Mapping

from jord.gdal_utilities import OGR
from warg import system_open_path


def write_csv(csv_file_name: Path, area_list: Sequence[Mapping]) -> None:
    if len(area_list) == 0:
        return

    fieldnames = list(area_list[0].keys())

    with open(csv_file_name, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for a in area_list:
            writer.writerow(a)


def area_of_layer(cad_file: Path) -> Optional[Dict]:
    a = None
    try:
        print(f"Opening cadfile: {cad_file}")
        # We use the MW_Floor_Area layer for floors that were delivered as cad files,
        # and triMeasuredGrossAreaLayer for floors that were delivered as dxf files from jpmc.
        area_layer_names = ["mw_floor_area", "trimeasuredgrossarealayer"]
        driver_name = "DXF"
        driver = OGR.GetDriverByName(driver_name)
        data_source = driver.Open(cad_file.as_posix(), 0)
        layer = data_source.GetLayer()
        area = 0
        number_of_building_polygons = 0

        for feature in layer:
            if feature.GetField("Layer").lower() in area_layer_names:
                g = feature.GetGeometryRef()
                if g.GetPointCount() > 2:
                    number_of_building_polygons += 1
                    ring = OGR.Geometry(OGR.wkbLinearRing)

                    for i in range(0, g.GetPointCount()):
                        p = g.GetPoint(i)
                        ring.AddPoint_2D(p[0], p[1])

                    p = g.GetPoint(0)
                    ring.AddPoint_2D(p[0], p[1])

                    poly = OGR.Geometry(OGR.wkbPolygon)
                    poly.AddGeometry(ring)
                    area = area + poly.Area()

        a = {
            "filepath": cad_file,
            "dirname": cad_file.parent,
            "filename": cad_file.name,
            "basename": cad_file.stem,
            "buildingnumber": number_of_building_polygons,
            "area square in": area,
            "area square feet": area
            / 144,  # 12 inch to a foot, 144 sq inch to a sq foot
        }

        layer.ResetReading()

        layer = None
        data_source = None
        del data_source

    except Exception as ex:
        print(ex)
        print(traceback.format_exc())

    return a


def run(root_dir: Path, out_path: Path) -> None:
    area_list = []
    for subdir, dirs, files in os.walk(root_dir):
        for file in files:
            if ".dxf" in file:
                area_list.append(area_of_layer(Path(Path(subdir) / file)))

    write_csv(out_path, area_list)

    system_open_path(out_path)


if __name__ == "__main__":
    run(Path("/mnt/cad"), Path("/mnt/cad"))
