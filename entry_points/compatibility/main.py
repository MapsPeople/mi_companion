#!/usr/bin/python
import logging

from integration_system.compatibilization.solution import (
    update_solution_external_id,
)


def run(*, solution_id: str) -> None:
    update_solution_external_id(solution_id, "pike-place-market-qgis")


if __name__ == "__main__":
    KEMPER_QGIS = "717003114802465c9793f5ff"
    PIKE_QGIS = "f26145495da3496e9ac6a7cf"

    logging.basicConfig(level=logging.INFO)

    run(solution_id=PIKE_QGIS)
