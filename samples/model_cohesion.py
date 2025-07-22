import shapely

from sync_module.shared.model.common_models import MIVenueType
from sync_module.model import (
    Area,
    Building,
    Floor,
    LanguageBundle,
    LocationType,
    Venue,
)
from jord.shapely_utilities import dilate

if __name__ == "__main__":
    venue = Venue(
        admin_id="asda",
        translations={"en": LanguageBundle(name="a")},
        polygon=dilate(shapely.Point((0, 0))),
        venue_type=MIVenueType.business_campus,
    )
    building = Building(
        admin_id="ijsad",
        polygon=dilate(shapely.Point((0, 0))),
        venue=venue,
        translations={"en": LanguageBundle(name="a")},
    )
    floor = Floor(
        floor_index=0,
        building=building,
        polygon=dilate(shapely.Point((0, 0))),
        translations={"en": LanguageBundle(name="a")},
    )
    area = Area(
        admin_id="ijsad",
        floor=floor,
        location_type=LocationType(
            admin_id="a", translations={"en": LanguageBundle(name="a")}
        ),
        polygon=dilate(shapely.Point((0, 0))),
        translations={"en": LanguageBundle(name="a")},
    )
