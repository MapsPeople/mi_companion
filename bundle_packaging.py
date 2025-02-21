import logging
import os
import shutil
import subprocess
import sys
import sysconfig
from multiprocessing import Pipe
from pathlib import Path
from subprocess import PIPE, Popen, STDOUT
from typing import Optional, Union

from mi_companion.constants import BUNDLED_PACKAGES_DIR, VERSION

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
    bundle_name: Union[str, Path],
    clean: bool = True,
    python_version: str = "3.12",
    version: Optional[str] = None,
    project_name: str = "MapsIndoors",
    platform: str = sysconfig.get_platform(),
) -> None:
    if isinstance(bundle_name, str):
        bundle_name = Path(bundle_name)
    if True:
        if bundle_name.exists():
            if clean:
                shutil.rmtree(bundle_name)

    if version is not None:
        version = version.replace(" ", "")
        assert (
            VERSION.replace(" ", "").lower() == version
        ), f"{VERSION}!={version}"  # JUST MAKE SURE!
        # bundle_name = bundle_name.with_stem(f"{bundle_name.stem}.{version}")

    bundle_name.mkdir(parents=True, exist_ok=True)

    submodule_directory = Path(__file__).parent.absolute()

    assert submodule_directory.exists()

    platform = platform.replace("-", "_").replace(".", "_")
    cp_version = python_version.replace(".", "")
    implementation = "cp"  # + cp_version

    os.environ["SUBMODULE_DIRECTORY"] = submodule_directory.as_posix()

    os.environ["ZMQ_PREFIX"] = "bundled"
    os.environ["ZMQ_BUILD_DRAFT"] = "1"

    abis = [
        "--abi",
        f"{implementation}{cp_version}m",
        "--abi",
        f"{implementation}{cp_version}",
        "--abi",
        "abi3",
        "--abi",
        "none",
    ]

    platforms = [
        "--platform",
        f"{platform}",
    ]  # "--platform", "any"]

    if True:
        catching_callable(
            [
                "pip",
                "install",
                "-U",
                "-t",
                f"{bundle_name}",
                "-r",
                f"{REQUIREMENTS_FILE}",
                "--break-system-packages",
                "--verbose",
                # "--no-build-isolation",
                "--only-binary",
                ":all:",
                "--implementation",
                implementation,
                "--python-version",
                python_version,
                # *abis,
                *platforms,
            ]
        )

    emit_additional_bundle_files(
        python_version=python_version,
        target_site_packages_dir=bundle_name,
        BUNDLE_VERSION=VERSION,
        BUNDLE_PROJECT_NAME=project_name,
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

description=A Python dependency bundle, please keep the matching version installed, you may prune the rest.
about=A bundle of Python dependencies for the MapsIndoors plugin

tracker=https://github.com/MapsPeople
repository=https://github.com/MapsPeople
homepage=https://github.com/MapsPeople

category=Web
icon=icon.png

hasProcessingProvider=no
experimental=True
deprecated=True

# Tags are comma separated with spaces allowed
tags=python, mapsindoors, companion
      """
        )

    with open(target_site_packages_dir / "__init__.py", "w") as f:
        f.write(
            f"""

class BundlePlugin:
  def tr(self, message):
    return QCoreApplication.translate('MI bundle', message)

  def initGui(self):
    ...

  def unload(self):
    ...

def classFactory(iface):
  return BundlePlugin()

          """
        )

    if (target_site_packages_dir / "LICENSE").exists():
        shutil.rmtree(target_site_packages_dir / "LICENSE", ignore_errors=True)
    shutil.copy(
        REQUIREMENTS_FILE.parent / "LICENSE", target_site_packages_dir / "LICENSE"
    )

    if (target_site_packages_dir / "icon.png").exists():
        shutil.rmtree(target_site_packages_dir / "icon.png", ignore_errors=True)
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
        "--python-version",
        help="Which python version",
        type=str,
        default=f"{sys.version_info.major}.{sys.version_info.minor}",
        required=False,
    )
    parser.add_argument(
        "--plugin-version",
        help="Which plugin version",
        type=str,
        default=None,
        required=False,
    )
    parser.add_argument(
        "--platform",
        help="Which platform to build bundle for",
        type=str,
        default=sysconfig.get_platform(),
        required=False,
    )
    parser.add_argument(
        "--target-dir",
        help="Where to install the packages",
        type=str,
        default=str(TARGET_DIR),
        required=False,
    )

    args = parser.parse_args()
    package_dependencies(
        bundle_name=args.target_dir,
        python_version=args.python_version,
        version=args.plugin_version,
        platform=args.platform,
        clean=False,
    )
