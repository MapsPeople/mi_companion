import logging
import os
import shutil
import subprocess
from enum import Enum
from pathlib import Path
from subprocess import PIPE, Popen, STDOUT

from mi_companion.constants import SHIPPED_PACKAGES_DIR

PLUGIN_DIR = Path("mi_companion")
REQUIREMENTS_FILE = PLUGIN_DIR / "requirements.txt"

a = PLUGIN_DIR / SHIPPED_PACKAGES_DIR
logger = logging.getLogger(__name__)


class PlatformEnum(Enum):
    windows = "Windows"
    # linux = 'Linux'
    # darwin = 'Darwin'


IGNORE_THIS = """

win_amd64

manylinux_2_28_x86_64
manylinux_2_28_aarch64
manylinux_2_17_x86_64
manylinux2014_x86_64
manylinux_2_17_armv7l
manylinux2014_armv7l
manylinux_2_17_aarch64
manylinux2014_aarch64

macosx_10_9_x86_64
macosx_11_0_arm64
macosx_10_9_universal2
macosx_10_7_x86_64
"""


def get_site_packages(platform_):
    if not isinstance(platform_, PlatformEnum):
        platform_ = PlatformEnum(platform_)

    return a / platform_.value.lower()


def log_subprocess_output(pipe):
    for line in iter(pipe.readline, b""):  # b'\n'-separated lines
        logger.info("got line from subprocess: %r", line)


def catching_callable(*args, **kwargs):
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


def package_packages(
    clean=True,
    # python_version ='3.9.0'
):
    if a.exists():
        if clean:
            shutil.rmtree(a)

    for p in PlatformEnum:
        target_site_packages_dir = a / p.value.lower()

        target_site_packages_dir.mkdir(parents=True, exist_ok=True)

        requirements_file_parent_directory = str(
            REQUIREMENTS_FILE.parent.absolute().as_posix()
        )

        os.environ["REQUIREMENTS_FILE_PARENT_DIRECTORY"] = (
            requirements_file_parent_directory
        )

        catching_callable(
            [
                f"pip",
                "install",
                "-U",
                f"-t",
                f"{target_site_packages_dir}",
                f"-r",
                f"{REQUIREMENTS_FILE}",
                f"--break-system-packages",
            ]
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.INFO)
    package_packages()
