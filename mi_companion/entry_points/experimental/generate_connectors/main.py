#!/usr/bin/python
import logging
from typing import Optional

from mi_companion import RESOURCE_BASE_PATH

_logger = logging.getLogger(RESOURCE_BASE_PATH)
__all__ = ["run"]
FUNCTION_DESCRIPTION = """...
"""
__doc__ = FUNCTION_DESCRIPTION


def run(*, a, b: Optional[str] = None, c: int = 1) -> None:
    print(f"Nice {a=} {b=} {c=}")
