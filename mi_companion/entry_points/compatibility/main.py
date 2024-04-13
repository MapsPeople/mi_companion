#!/usr/bin/python
import logging


logger = logging.getLogger(__name__)


def run(*, solution_id: str) -> None:
    from integration_system.compatibilization import (
        make_solution_compatible,
    )

    logger.info(f"Running compatiblisation on {solution_id=}")

    make_solution_compatible(solution_id)

    logger.info(f"Finished compatiblisation on {solution_id=}")


if __name__ == "__main__":

    def asijdauh():
        kemper_qgis = "717003114802465c9793f5ff"

        logger.basicConfig(level=logging.INFO)

        run(solution_id=kemper_qgis)
