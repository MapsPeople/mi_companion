#!/usr/bin/python
import logging
from typing import Optional

from mi_companion import RESOURCE_BASE_PATH

logger = logging.getLogger(RESOURCE_BASE_PATH)
__all__ = ["run"]


def run(*, a: str, b: Optional[str] = None, c: int = 1) -> None:
    print(f"Nice {a=} {b=} {c=}")
