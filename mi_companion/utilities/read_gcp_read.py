import csv
from typing import Generator, Tuple

__all__ = ["read_gcp_file"]


def read_gcp_file(
    gcp_points_file_path, filter_comments: bool = True
) -> Tuple[Generator, Generator]:
    with open(gcp_points_file_path, encoding="utf8", errors="ignore") as fp:
        if filter_comments:
            fp = filter(lambda row: row[0] != "#", fp)

        gcps = list(csv.DictReader(fp, delimiter=","))

    source_xy, dest_xy = zip(
        *(
            (
                (float(d["sourceX"]), float(d["sourceY"])),
                (float(d["mapX"]), float(d["mapY"])),
            )
            for d in gcps
            if int(d["enable"]) > 0
        )
    )
    return source_xy, dest_xy


if __name__ == "__main__":
    source_xy, dest_xy = read_gcp_file(r"C:\Users\chen\Documents\asdad.gpkg.points")

    print(list(source_xy), list(dest_xy))
