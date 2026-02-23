import logging

from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtWidgets import (
    QMessageBox,
)
from qgis.core import (
    QgsField,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
)
from qgis.utils import iface

from jord.qgis_utilities import LayerEditingContext
from mi_plugin import RESOURCE_BASE_PATH
from mi_plugin.layer_descriptors import (
    LAYER_DESCRIPTORS_WITH_TRANSLATIONS,
    SOLUTION_DATA_DESCRIPTOR,
)
from jord.qgis_utilities.compatability import cancel_button, ok_button

_logger = logging.getLogger(RESOURCE_BASE_PATH)

__all__ = ["run"]
TRANSLATIONS_FIELD_NAME = "translations"
FUNCTION_DESCRIPTION = """    language_code field below: Add language, e.g. en, da, de, fr
"""

__doc__ = FUNCTION_DESCRIPTION


def run(
    *,
    language_code: str,
    # copy_from_language: str = "en",
    # fallback_value: str = "NoName",
    # , auto_translate: bool=False
) -> bool:
    f"""{FUNCTION_DESCRIPTION}


    """
    copy_from_language: str = "en"
    fallback_value: str = "NoName"

    if language_code == copy_from_language:
        QtWidgets.QMessageBox.warning(
            None,
            "'en' already exists",
            "'en' already exists. Please specify a different language_code",
        )
        return False
    if language_code == "":
        QtWidgets.QMessageBox.warning(
            None,
            "No language_code",
            "Please specify a language_code",
        )
        return False

    selected_nodes = iface.layerTreeView().selectedNodes()

    responses = {}
    if len(selected_nodes) == 1:  # TODO: SHOULD WE ALLOW MORE?
        for node in selected_nodes:
            responses = recursive_add_language_to_group(
                node, language_code, fallback_value, copy_from_language
            )

    else:
        QtWidgets.QMessageBox.warning(
            None,
            "Select only one item",
            "Make sure to select exactly one group or layer (not multiple or none)",
        )
        return False

    if True in responses.values():
        true_items = [key for key, value in responses.items() if value]

        QtWidgets.QMessageBox.information(
            None,
            "Success",
            f"We added language {TRANSLATIONS_FIELD_NAME}.{language_code}.name to {len(true_items)} layers.",
        )
    else:
        QtWidgets.QMessageBox.warning(
            None,
            "No update",
            f"Nothing was added to the selected layer/group.",
        )
    return True


def add_translation_language_field_to_layer(
    node, language_code: str, fallback_value: str, copy_from_language: str
) -> dict[str, bool]:
    """

    :param node:
    :type node:
    :param language_code:
    :type language_code:
    :param fallback_value:
    :type fallback_value:
    :param copy_from_language:
    :type copy_from_language:
    :return:
    :rtype:
    """
    current_layer = node.layer()  # QgisVectorLayer
    should_add_translation = False
    layer_name = node.name()
    for descriptor in LAYER_DESCRIPTORS_WITH_TRANSLATIONS:
        if descriptor in layer_name:
            should_add_translation = True
            break

    if not should_add_translation:
        return {}

    layer_fields = current_layer.fields()
    layer_names = layer_fields.names()

    ### Check if provided language_code already exists
    if f"{TRANSLATIONS_FIELD_NAME}.{language_code}.name" in layer_names:
        msg = f"The layer {layer_name} already has the '{language_code}' language. Do you want to overwrite it?"
        reply = QMessageBox.question(
            None, "language_code exists", msg, ok_button, cancel_button
        )

        if reply == QMessageBox.Cancel:
            return {layer_name: False}

    ### Check if inputvalues are provided and change booleans accordingly.
    default_language_exists = False
    fallback_value_exists = False

    if f"{TRANSLATIONS_FIELD_NAME}.{copy_from_language}.name" in layer_names:
        default_language_exists = True
    elif fallback_value:
        fallback_value_exists = True

        ### Also let user know that copy_from_language does not exist, hence you ask if they wanna use the fallback_value.
        msg = f"The layer {layer_name} does not have '{copy_from_language}' language to copy from. Do you want to populate all features with '{fallback_value}' instead?"
        reply = QMessageBox.question(None, "QGIS plugin", msg, ok_button, cancel_button)

        if reply == QMessageBox.Cancel:
            return {layer_name: False}

    else:
        QtWidgets.QMessageBox.warning(
            None,
            "Missing attribute",
            f"The layer {layer_name} does not have a {TRANSLATIONS_FIELD_NAME}.{copy_from_language}.name attribute. Please specify a fallback_value (e.g. NoName).",
        )
        return {layer_name: False}

    # Start editing the layer
    with LayerEditingContext(f"Add {language_code}", current_layer):
        field_name = f"{TRANSLATIONS_FIELD_NAME}.{language_code}.name"
        # Create a new field
        new_field = QgsField(field_name, QVariant.String)  # Change type as needed

        # Add the field to the layer
        current_layer.addAttribute(new_field)
        if default_language_exists:
            for feature in current_layer.getFeatures():
                feature[field_name] = feature[
                    f"{TRANSLATIONS_FIELD_NAME}.{copy_from_language}.name"
                ]
                current_layer.updateFeature(feature)
        elif fallback_value_exists:
            for feature in current_layer.getFeatures():
                feature[field_name] = fallback_value
                current_layer.updateFeature(feature)

    return {layer_name: True}


def recursive_add_language_to_group(
    node, language_code: str, fallback_value: str, copy_from_language: str
) -> dict[str, bool]:
    """

    :param node:
    :type node:
    :param language_code:
    :type language_code:
    :param fallback_value:
    :type fallback_value:
    :param copy_from_language:
    :type copy_from_language:
    :return:
    :rtype:
    """
    responses = {}
    if isinstance(node, QgsLayerTreeLayer):
        response = add_translation_language_field_to_layer(
            node, language_code, fallback_value, copy_from_language
        )
        solution_response = add_language_code_to_solutiondata(node, language_code)
        responses.update(response)
        responses.update(solution_response)

    elif isinstance(node, QgsLayerTreeGroup):
        for child in node.children():
            response = recursive_add_language_to_group(
                child, language_code, fallback_value, copy_from_language
            )
            responses.update(response)

    else:
        logging.error(
            f"This should not happen as node must either be a QgsLayerTreeLayer or a QgsLayerTreeGroup."
        )
    return responses


def add_language_code_to_solutiondata(node, language_code: str) -> dict[str, bool]:
    """

    :param node:
    :type node:
    :param language_code:
    :type language_code:
    :return:
    :rtype:
    """
    layer = node.layer()  # QgisVectorLayer

    layer_name = node.name()

    if SOLUTION_DATA_DESCRIPTOR in layer_name:

        # Get the first feature (assuming there's only one)
        feature = next(layer.getFeatures())

        # Get the current list of languages
        field_index = layer.fields().indexFromName("available_languages")
        languages = feature["available_languages"]

        # If the field is empty or NULL, initialize an empty list
        if not languages:
            languages = []

        # Check if the language already exists
        if language_code not in languages:

            with LayerEditingContext(f"Add {language_code}", layer):
                # Add the new language
                languages.append(language_code)

                layer.changeAttributeValue(feature.id(), field_index, languages)
                print(f"Added {language_code} to languages list")
        else:
            print(f"{language_code} already in languages list")
            return {layer_name: False}

        return {layer_name: True}

    return {}


if __name__ == "__main__":

    def asijdauh():
        """ """
        kemper_qgis = "4b2592bdd05342f2ada9cca3"

        run(language="th")

    asijdauh()
