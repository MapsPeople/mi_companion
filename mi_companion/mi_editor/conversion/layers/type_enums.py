from enum import Enum


__all__ = ["InventoryTypeEnum"]


class InventoryTypeEnum(Enum):
    room = "rooms"
    poi = "pois"
    area = "areas"
