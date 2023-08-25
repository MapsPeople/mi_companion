#!/usr/bin/python
# -*- coding: utf-8 -*-


import csv
import os
import traceback
from pathlib import Path
from typing import List, Iterable, Sequence

from jord.gdal_utilities import GDAL, OGR


def write_csv(path: Path, area_list: Sequence) -> None:
    if len(area_list) == 0:
        return

    fieldnames = []
    for f in area_list[0]:
        fieldnames.append(f)

    csv_file_name = path / "cadareareport.csv"

    with open(csv_file_name, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for a in area_list:
            writer.writerow(a)


def area_of_layer(cad_file: Path) -> List:
    area_list = []

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

        area_list.append(a)

    except Exception as ex:
        print(ex)
        print(traceback.format_exc())

    return area_list


def run(root_dir: Path):
    jobs = []

    for subdir, dirs, files in os.walk(root_dir):
        for file in files:
            if ".dxf" in file:
                cad_path = os.path.join(subdir, file)
                jobs.append(cad_path)

    area_list = []
    for j in jobs:
        if not j in [r""]:
            area_list.append(area_of_layer(Path(j)))

    write_csv(root_dir, area_list)


if __name__ == "__main__":
    run(Path("/mnt/cad"))
