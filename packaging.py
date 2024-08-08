import logging
import os
import shutil
import subprocess
from multiprocessing import Pipe
from pathlib import Path
from subprocess import PIPE, Popen, STDOUT

from mi_companion.constants import BUNDLED_PACKAGES_DIR

THIS_DIR = Path(__file__).parent
TARGET_DIR = THIS_DIR / BUNDLED_PACKAGES_DIR
PLUGIN_DIR = THIS_DIR / "mi_companion"
REQUIREMENTS_FILE = PLUGIN_DIR / "requirements.txt"

logger = logging.getLogger(__name__)


def log_subprocess_output(pipe: Pipe) -> None:
    for line in iter(pipe.readline, b""):  # b'\n'-separated lines
        logger.info("got line from subprocess: %r", line)


def catching_callable(*args, **kwargs) -> None:
    try:
        logger.info(f"{list(args)}, {list(kwargs.items())}")

        process = Popen(*args, **kwargs, stdout=PIPE, stderr=STDOUT)
        with process.stdout:
            log_subprocess_output(process.stdout)
        exitcode = process.wait()  # 0 means success
        if exitcode:
            logger.info("Success")

    except subprocess.CalledProcessError as e:
        output = (e.stderr, e.stdout, e)
        logger.warning(output)


def package_dependencies(
    target_site_packages_dir: Path,
    clean: bool = True,
) -> None:
    if target_site_packages_dir.exists():
        if clean:
            shutil.rmtree(target_site_packages_dir)

    target_site_packages_dir.mkdir(parents=True, exist_ok=True)

    submodule_directory = str(REQUIREMENTS_FILE.parent.parent.absolute().as_posix())

    os.environ["SUBMODULE_DIRECTORY"] = submodule_directory

    os.environ["ZMQ_PREFIX"] = "bundled"
    os.environ["ZMQ_BUILD_DRAFT"] = "1"

    catching_callable(
        [
            "pip",
            "install",
            "-U",
            "-t",
            f"{target_site_packages_dir}",
            "-r",
            f"{REQUIREMENTS_FILE}",
            "--break-system-packages",
            "--verbose",
            "--no-binary",
            "pyzmq",
            # "--no-build-isolation",
        ]
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.INFO)
    package_dependencies(TARGET_DIR)
