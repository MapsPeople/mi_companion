#!/usr/bin/python
import logging
from typing import Optional

logger = logging.getLogger(__name__)
__all__ = []


def run(*, a, b: Optional[str] = None, c: int = 1) -> None:
    print(f"Nice {a=} {b=} {c=}")
