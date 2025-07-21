import dataclasses
import shapely
from pandas.io.json._normalize import _simple_json_normalize

from integration_system.model import Solution
from integration_system.model.typings import LanguageBundle
from jord.shapely_utilities import dilate

solution = Solution("s", "s", "s")

venue_key = solution.add_venue(
    "vadmin",
    dilate(shapely.Point((0, 0))),
    translations={
        "en": LanguageBundle(name="v1"),
        "de": LanguageBundle(name="hurensohn"),
    },
)


# print(_simple_json_normalize(dataclasses.asdict(solution.venues.get(venue_key))))


print(
    _simple_json_normalize(
        {
            language: dataclasses.asdict(lb)
            for language, lb in solution.venues.get(venue_key).translations.items()
        }
    )
)


# print(json_normalize(dataclasses.asdict(solution.venues.get(venue_key))))
