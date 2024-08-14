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

MIN_QGIS_VERSION = "3.38"

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
    *,
    target_site_packages_dir: Path,
    clean: bool = True,
    python_version: str = "3.9",
    BUNDLE_VERSION="0.0.1",
    BUNDLE_PROJECT_NAME="MapsIndoors",
) -> None:
    if True:
        if target_site_packages_dir.exists():
            if clean:
                shutil.rmtree(target_site_packages_dir)

    target_site_packages_dir.mkdir(parents=True, exist_ok=True)

    submodule_directory = Path(__file__).parent.absolute()

    assert submodule_directory.exists()

    os.environ["SUBMODULE_DIRECTORY"] = submodule_directory.as_posix()

    os.environ["ZMQ_PREFIX"] = "bundled"
    os.environ["ZMQ_BUILD_DRAFT"] = "1"

    if True:
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
                # --platform manylinux2014_x86_64
                # "--no-binary",
                # "pyzmq",
                # "--no-build-isolation",
                "--only-binary",
                ":all:",
                "--implementation",
                "cp",
                "--python-version",
                python_version,
            ]
        )

    emit_additional_bundle_files(
        python_version=python_version,
        target_site_packages_dir=target_site_packages_dir,
        BUNDLE_VERSION=BUNDLE_VERSION,
        BUNDLE_PROJECT_NAME=BUNDLE_PROJECT_NAME,
    )


def emit_additional_bundle_files(
    *,
    python_version: str,
    target_site_packages_dir: Path,
    BUNDLE_VERSION: str = "0.0.1",
    BUNDLE_PROJECT_NAME: str = "MapsIndoors",
) -> None:
    with open(target_site_packages_dir / "metadata.txt", "w") as f:
        f.write(
            f"""[general]
name={BUNDLE_PROJECT_NAME} Python {python_version} bundle
qgisMinimumVersion={MIN_QGIS_VERSION}
#qgisMaximumVersion=3.38
version={BUNDLE_VERSION}

author=heider
email=chen@mapspeople.com

description=A Python dependency bundle
about=A bundle of Python dependencies for the MapsIndoors plugin

tracker=https://github.com/MapsPeople
repository=https://github.com/MapsPeople
homepage=https://github.com/MapsPeople

category=Web
icon=icon.png

hasProcessingProvider=no
experimental=False

# Tags are comma separated with spaces allowed
tags=python, mapsindoors, companion
      """
        )

    (target_site_packages_dir / "__init__.py").touch()

    if (target_site_packages_dir / "LICENSE").exists():
        shutil.rmtree(target_site_packages_dir / "LICENSE")
    shutil.copy(
        REQUIREMENTS_FILE.parent / "LICENSE", target_site_packages_dir / "LICENSE"
    )

    if (target_site_packages_dir / "icon.png").exists():
        shutil.rmtree(target_site_packages_dir / "icon.png")
    shutil.copy(
        REQUIREMENTS_FILE.parent / "icon.png", target_site_packages_dir / "icon.png"
    )


# from importlib.metadata import files
# [file for file in files('pydantic-core') if file.name.startswith('_pydantic_core')]

# import sysconfig
# sysconfig.get_config_var("EXT_SUFFIX")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.INFO)
    import argparse

    parser = argparse.ArgumentParser("simple_example")
    parser.add_argument(
        "--python_version",
        help="Which python version",
        type=str,
        default="3.9",
        required=False,
    )
    # parser.add_argument("plugin_name", help="Which plugin to bundle dependencies", type=str)
    parser.add_argument(
        "--plugin_version",
        help="Which plugin version",
        type=str,
        default="0.0.1",
        required=False,
    )

    args = parser.parse_args()
    package_dependencies(
        target_site_packages_dir=TARGET_DIR,
        python_version=args.python_version,
        BUNDLE_VERSION=args.plugin_version,  # BUNDLE_PROJECT_NAME=args.plugin_name
    )
