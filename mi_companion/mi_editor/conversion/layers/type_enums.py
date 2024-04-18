from enum import Enum


__all__ = ["InventoryTypeEnum"]


class InventoryTypeEnum(Enum):
    ROOM = "rooms"
    POI = "pois"
    AREA = "areas"
