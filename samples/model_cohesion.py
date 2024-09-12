import shapely
from jord.shapely_utilities import dilate

from integration_system.model import (
    Area,
    Building,
    Floor,
    LocationType,
    Venue,
    VenueType,
)

if __name__ == "__main__":
    venue = Venue(
        admin_id="asda",
        name="asodj",
        polygon=dilate(shapely.Point((0, 0))),
        venue_type=VenueType.business_campus,
    )
    building = Building(
        admin_id="ijsad",
        polygon=dilate(shapely.Point((0, 0))),
        venue=venue,
        name="isjad",
    )
    floor = Floor(
        floor_index=0,
        building=building,
        name="ijasddd",
        polygon=dilate(shapely.Point((0, 0))),
    )
    area = Area(
        admin_id="ijsad",
        floor=floor,
        location_type=LocationType(name="iajsd"),
        name="ijasddd",
        polygon=dilate(shapely.Point((0, 0))),
    )
