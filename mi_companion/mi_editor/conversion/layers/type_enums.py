from enum import Enum

__all__ = ["LocationTypeEnum"]


class LocationTypeEnum(Enum):
    ROOM = "rooms"
    POI = "pois"
    AREA = "areas"
