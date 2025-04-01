import logging
from typing import Any, Mapping

# noinspection PyUnresolvedReferences
from qgis.PyQt.QtCore import QVariant

from integration_system.model import ConnectionType, DoorType, EntryPointType

logger = logging.getLogger(__name__)

__all__ = ["get_door_type", "get_entry_point_type", "get_connection_type"]


def get_door_type(door_attributes: Mapping[str, Any]) -> DoorType:
    """

    :param door_attributes:
    :return:
    """
    door_type = door_attributes["door_type"]

    if isinstance(door_type, str):
        ...
    elif isinstance(door_type, QVariant):
        # logger.warning(f"{typeToDisplayString(type(v))}")
        if door_type.isNull():  # isNull(v):
            door_type = None
        else:
            door_type = door_type.value()

    return DoorType(int(door_type))


def get_entry_point_type(entry_point_attributes: Mapping[str, Any]) -> EntryPointType:
    """

    :param entry_point_attributes:
    :return:
    """
    try:
        entry_point_type = entry_point_attributes["entry_point_type"]
    except Exception as e:
        logger.error(e)
        logger.error(entry_point_attributes)
        logger.error(f"Defaulting to EntryPointType.any")
        entry_point_type = EntryPointType.any.value
        # raise e

    if isinstance(entry_point_type, str):
        ...
    elif isinstance(entry_point_type, QVariant):
        # logger.warning(f"{typeToDisplayString(type(v))}")
        if entry_point_type.isNull():  # isNull(v):
            entry_point_type = None
        else:
            entry_point_type = entry_point_type.value()

    return EntryPointType(int(entry_point_type))


def get_connection_type(connector_attributes: Mapping[str, Any]) -> ConnectionType:
    """

    :param connector_attributes:
    :return:
    """
    connection_type = connector_attributes["connection_type"]

    if isinstance(connection_type, str):
        ...
    elif isinstance(connection_type, QVariant):
        # logger.warning(f"{typeToDisplayString(type(v))}")
        if connection_type.isNull():  # isNull(v):
            connection_type = None
        else:
            connection_type = connection_type.value()

    return ConnectionType(int(connection_type))
