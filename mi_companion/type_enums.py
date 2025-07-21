from enum import Enum

__all__ = ["BackendLocationTypeEnum"]


class BackendLocationTypeEnum(Enum):
    ROOM = "rooms"
    POI = "pois"
    AREA = "areas"
