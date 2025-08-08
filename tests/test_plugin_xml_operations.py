# Standard library
import sys
from pathlib import Path
import tempfile

# Third-party imports
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plugin_xml_operations as pxo


@pytest.fixture
def inputs_dir():
    return Path("inputs").as_posix()


def test_read_gcs_plugin_versions(inputs_dir):
    gcs_plugins_file = Path(inputs_dir) / "gcs-plugins.txt"
    gcs_plugins_set = pxo.read_gcs_plugin_versions(gcs_plugins_file)
    print(gcs_plugins_set)

    # Check the contents of the set
    assert len(gcs_plugins_set) == 2
    assert "0.7.20" in gcs_plugins_set
    assert "0.7.20-rc44" not in gcs_plugins_set
    assert "0.7.20-exp-merge-xmls-8" in gcs_plugins_set


def test_merge_xml(inputs_dir):
    file1 = Path(inputs_dir) / "plugin_one.xml"
    file2 = Path(inputs_dir) / "plugin_two.xml"
    merged_file = Path(inputs_dir) / "plugin_merged.xml"

    pxo.merge_xml(str(file1), str(file2), str(merged_file))

    # Check the merged output
    with open(merged_file, "r") as merged_file:
        merged_content = merged_file.read()
        assert merged_content.count("<pyqgis_plugin") == 4
        assert (
            '<pyqgis_plugin name="MapsIndoors Beta" version="0.7.20">' in merged_content
        )
        assert (
            '<pyqgis_plugin name="MapsIndoors Beta" version="0.7.20-rc44">'
            in merged_content
        )
        assert (
            '<pyqgis_plugin name="MapsIndoors Beta" version="0.7.20-deprecated">'
            in merged_content
        )
        assert (
            '<pyqgis_plugin name="MapsIndoors Beta" version="0.7.20-exp-merge-xmls-8">'
            in merged_content
        )


def test_remove_missing_plugins_from_gcs(inputs_dir):
    xml_file = Path(inputs_dir) / "plugin_merged.xml"
    gcs_plugins = Path(inputs_dir) / "gcs-plugins.txt"

    # Create a temporary file to write the modified XML
    with tempfile.NamedTemporaryFile(
        delete=False, mode="w", suffix=".xml"
    ) as temp_file:
        temp_file_path = temp_file.name

    gcs_plugins_set = pxo.read_gcs_plugin_versions(gcs_plugins)
    pxo.remove_missing_plugins_from_gcs(xml_file, gcs_plugins_set, temp_file_path)

    # Check the modified XML
    with open(temp_file_path, "r") as modified_file:
        modified_content = modified_file.read()
        assert (
            '<pyqgis_plugin name="MapsIndoors Beta" version="0.7.20">'
            in modified_content
        )
        assert (
            '<pyqgis_plugin name="MapsIndoors Beta" version="0.7.20-rc44">'
            not in modified_content
        )
        assert (
            '<pyqgis_plugin name="MapsIndoors Beta" version="0.7.20-exp-merge-xmls-8">'
            in modified_content
        )

    # Clean up the temporary file
    Path(temp_file_path).unlink()


def test_remove_deprecated_plugins_from_file(inputs_dir):
    xml_file = Path(inputs_dir) / "plugin_two.xml"

    # Create a temporary file to write the modified XML
    with tempfile.NamedTemporaryFile(
        delete=False, mode="w", suffix=".xml"
    ) as temp_file:
        temp_file_path = temp_file.name

    pxo.remove_deprecated_plugins_from_file(xml_file, temp_file_path)

    # Check the modified XML
    with open(temp_file_path, "r") as modified_file:
        modified_content = modified_file.read()
        assert (
            '<pyqgis_plugin name="MapsIndoors Beta" version="0.7.20-rc44">'
            in modified_content
        )
        assert (
            '<pyqgis_plugin name="MapsIndoors Beta" version="0.7.20-deprecated">'
            not in modified_content
        )
        assert (
            '<pyqgis_plugin name="MapsIndoors Beta" version="0.7.20-exp-merge-xmls-8">'
            in modified_content
        )

    # Clean up the temporary file
    Path(temp_file_path).unlink()


def test_version_dash_determines_experimental_status(inputs_dir):
    """
    Test that plugins with exactly one dash in their version are marked as experimental,
    while plugins with zero or multiple dashes are not marked as experimental.
    """
    from lxml import etree

    xml_file = Path(inputs_dir) / "plugin_two.xml"
    tree = etree.parse(str(xml_file))
    root = tree.getroot()
    if root.tag != "plugins":
        raise ValueError(f"Root element must be 'plugins', found '{root.tag}'")
    for plugin in root.findall("pyqgis_plugin"):
        version = plugin.attrib.get("version", "")
        experimental_elem = plugin.find("experimental", "")
        if experimental_elem is not None:
            is_experimental = experimental_elem.text.lower() == "true"
            dash_count = version.count("-")
            # One dash should make it experimental
            expected_experimental = dash_count == 1
            assert is_experimental == expected_experimental
