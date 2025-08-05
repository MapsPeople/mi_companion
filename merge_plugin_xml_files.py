import sys
from typing import Iterable, Set
from lxml import etree


def _process_file(
    file: str,
    merged_root: etree._Element,
    parsed_versions: Set[str]
) -> None:
    """ Process a single XML file and append unique pyqgis_plugin elements to the merged root. """
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
        input_files: Iterable[str],
        merged_root: etree._Element,
        parsed_versions: Set[str]
) -> None:
    """ Append unique plugins from multiple XML files to the merged root element. """
    for file in input_files:
        _process_file(file, merged_root, parsed_versions)

def merge_xml(file1: str, file2: str, output: str) -> None:
    """ Merge two XML files containing QGIS plugin definitions. """
    merged_root = etree.Element("plugins")
    parsed_versions = set()
    append_unique_plugins([file1, file2], merged_root, parsed_versions)
    tree = etree.ElementTree(merged_root)
    tree.write(output, pretty_print=True, xml_declaration=True, encoding="UTF-8")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(
            "Usage: python merge_plugin_xml_files.py file_one.xml file_two.xml merged_file.xml"
        )
        sys.exit(1)
    merge_xml(sys.argv[1], sys.argv[2], sys.argv[3])
