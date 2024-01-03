#!/usr/bin/python


import csv
import os
import traceback
from pathlib import Path
from typing import List, Optional, Sequence, Dict, Mapping

from jord.gdal_utilities import OGR
from warg import system_open_path


def run(*, a, b: Optional[str] = None, c: int = 1) -> None:
    print(f"Nice {a=} {b=} {c=}")
