#!/usr/bin/python
import logging
import os
import traceback
from pathlib import Path
from typing import Collection, Dict, Mapping, Optional

from mi_companion import PROJECT_APP_PATH

logger = logging.getLogger(__name__)

__all__ = []


def write_csv(csv_file_name: Path, area_list: Collection[Mapping]) -> None:
    if len(area_list) == 0:
        return

    fieldnames = list(area_list[0].keys())

    import csv

    with open(csv_file_name, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for a in area_list:
            writer.writerow(a)


def area_of_layer(cad_file: Path) -> Optional[Dict]:
    from jord.gdal_utilities import OGR

    a = None
    try:
        print(f"Opening cadfile: {cad_file}")
        possible_area_layer_names = [
            "mw_floor_area",
            "trimeasuredgrossarealayer",  # Tririga
            # 'Building-Perimeter',
            # "Area-External",
            # "Area - Gross External",
            # 'Area-GrossInternal',
            # 'Area-NetUsable',
            # 'RoomOutlines'
        ]
        driver_name = "DXF"
        driver = OGR.GetDriverByName(driver_name)
        data_source = driver.Open(cad_file.as_posix(), 0)
        layer = data_source.GetLayer()
        area = 0
        number_of_building_polygons = 0

        match = False
        for layer_name in [x.lower() for x in possible_area_layer_names]:
            if False:
                if match:
                    break

            for feature in layer:
                if feature.GetField("Layer").lower() in layer_name:
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
                        match = True

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
        logger.error(ex)
        logger.error(traceback.format_exc())

    return a


def run(
    root_dir: Path,
    out_path: Path,
    oda_converter_path: Optional[Path] = Path(
        r"C:\Program Files\ODA\ODAFileConverter 25.4.0\ODAFileConverter.exe"
    ),
) -> None:
    area_list = []
    if oda_converter_path is not None:
        if isinstance(oda_converter_path, str):
            oda_converter_path = Path(oda_converter_path)
            assert (
                oda_converter_path.exists()
            ), f"{oda_converter_path} is not a valid path"

    for subdir, dirs, files in os.walk(root_dir):
        for file in files:
            a = Path(subdir) / file
            if "dxf" in a.suffix:
                area_list.append(area_of_layer(a))
            elif "dwg" in a.suffix:
                from jord.cad_utilities import convert_to_dxf

                new_dxf_path: Path = convert_to_dxf(
                    a,
                    oda_converter_path,
                    target_dir=PROJECT_APP_PATH.user_cache / "cad_area",
                )

                logger.info(f"Emitted {new_dxf_path}")

                area_list.append(area_of_layer(Path(Path(subdir) / file)))
            else:
                logger.error(f"Skipping {a}")

    write_csv(out_path, area_list)

    from warg import system_open_path

    system_open_path(out_path)


if __name__ == "__main__":
    run(Path("/mnt/cad"), Path("/mnt/cad"))
