#!/usr/bin/python


from typing import Optional

from pathlib import Path


def run(*, a, b: Optional[str] = None, c: int = 1) -> None:
    from svaguely import parse_svg
    from warg import flatten_mapping

    exclude_dir = Path("")
    svg_elements, _ = parse_svg(exclude_dir / "svg_file_name", output_space=1)

    svg_elements = flatten_mapping(svg_elements)
