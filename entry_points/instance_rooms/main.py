#!/usr/bin/python


from typing import Optional


def run(*, a, b: Optional[str] = None, c: int = 1) -> None:
    print(f"Nice {a=} {b=} {c=}")
