import sys
from typing import Iterable, Set
from lxml import etree


def _process_file(
    file: str, merged_root: etree._Element, parsed_versions: Set[str]
) -> None:
    """Process a single XML file and append unique pyqgis_plugin elements to the merged root."""
    tree = etree.parse(file)
    root = tree.getroot()
    if root.tag != "plugins":
        raise ValueError(f"Root element must be 'plugins', found '{root.tag}'")
    for pyqgis_plugin in root.findall("pyqgis_plugin"):
        current_version = pyqgis_plugin.attrib.get("version", "unknown_version")
        if current_version not in parsed_versions:
            parsed_versions.add(current_version)
            merged_root.append(pyqgis_plugin)


def append_unique_plugins(
    input_files: Iterable[str], merged_root: etree._Element, parsed_versions: Set[str]
) -> None:
    """Append unique plugins from multiple XML files to the merged root element."""
    for file in input_files:
        _process_file(file, merged_root, parsed_versions)


def remove_deprecated_plugins(tree: etree._ElementTree) -> None:
    """Remove deprecated plugins from the XML tree."""
    for plugin in tree.xpath("//pyqgis_plugin[@deprecated='true']"):
        plugin.getparent().remove(plugin)


def remove_deprecated_plugins_from_file(file: str) -> None:
    """Remove deprecated plugins from a given XML file."""
    tree = etree.parse(file)
    remove_deprecated_plugins(tree)
    tree.write(file, pretty_print=True, xml_declaration=True, encoding="UTF-8")


def remove_missing_plugins_from_gcs(xml_file: str, gcs_plugins: Set[str]) -> None:
    """Remove plugins from the XML file that are no longer present on the GCS bucket."""
    tree = etree.parse(xml_file)
    root = tree.getroot()
    if root.tag != "plugins":
        raise ValueError(f"Root element must be 'plugins', found '{root.tag}'")

    # Iterate through each plugin in the XML file
    for plugin in root.findall("pyqgis_plugin"):
        plugin_version = plugin.attrib.get("version", "")
        if not plugin_version:
            print("Skipping plugin with no version attribute.")
            continue
        # Check if the plugin name is in the GCS plugins list
        if plugin_version not in gcs_plugins:
            print(
                f"Removing plugin {plugin_version} as it is not in the GCS plugins list."
            )
            # Remove the plugin element from the root
            root.remove(plugin)

    tree.write(xml_file, pretty_print=True, xml_declaration=True, encoding="UTF-8")


def merge_xml(file1: str, file2: str, output: str) -> None:
    """Merge two XML files containing QGIS plugin definitions.

    This is used by the release_qgis_plugin.py script to merge the existing plugin.xml files from the
    QGIS Plugin on GCS and the QGIS Bundle Plugin on GitHub Runner into a single plugin.xml file.
    The merged file will contain unique pyqgis_plugin elements based on their version attribute.
    """
    merged_root = etree.Element("plugins")
    parsed_versions = set()
    append_unique_plugins([file1, file2], merged_root, parsed_versions)
    tree = etree.ElementTree(merged_root)
    tree.write(output, pretty_print=True, xml_declaration=True, encoding="UTF-8")


if __name__ == "__main__":
    if sys.argv[1] not in ["merge", "remove_deprecated", "remove_missing"]:
        print(f"Unknown operation: {sys.argv[1]}")
        sys.exit(1)
    elif sys.argv[1] == "merge":
        if len(sys.argv) != 5:
            print(
                "Usage: python plugin_xml_operations.py merge file_one.xml file_two.xml merged_file.xml"
            )
            sys.exit(1)
        merge_xml(sys.argv[2], sys.argv[3], sys.argv[4])
    elif sys.argv[1] == "remove_missing":
        if len(sys.argv) != 4:
            print(
                "Usage: python plugin_xml_operations.py remove_missing file_one.xml gcs-plugins-list.txt"
            )
            sys.exit(1)
        # Read the GCS plugins list from the file, assuming each line contains a plugin version
        with open(sys.argv[3]) as gcs_plugins_txt:
            gcs_plugins_set = set()
            for line in gcs_plugins_txt:
                if line.strip():
                    try:
                        # Extract the version from the line, assuming it follows a specific format
                        version = (
                            line.strip()
                            .split("/")[-1]
                            .split("mi_companion.")[1]
                            .split(".zip")[0]
                        )
                    except IndexError:
                        continue
                    # Add the version to the set
                    if version:
                        gcs_plugins_set.add(version)

            remove_missing_plugins_from_gcs(sys.argv[2], gcs_plugins_set)
