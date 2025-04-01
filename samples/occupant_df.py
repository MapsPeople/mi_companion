from itertools import tee
from typing import Iterable, Mapping

from jord.pandas_utilities import df_to_columns
from jord.typing_utilities import solve_attribute_uri

from integration_system.mi import get_remote_solution
from integration_system.model import Venue
from integration_system.pandas_serde import collection_to_df

a = get_remote_solution(
    "fjordhaven7",
    venue_keys=[Venue.compute_key(admin_id="4255def5cf69540d70620fb7f60a5530bb0a18af")],
)

ls = collection_to_df(a.rooms)
os = collection_to_df(a.occupants)

ls["occupant"] = ls.index.map(lambda x: x if x in os.index else None)

columns = df_to_columns(ls)

if isinstance(columns, Mapping):
    attr_generator, attr_type_sampler = tee(iter(columns.values()))
elif isinstance(columns, Iterable):
    attr_generator, attr_type_sampler = tee(iter(columns))
else:
    raise TypeError(f"columns must be a mapping or an iterable of mappings")

field_type_configuration, fields, num_cols = solve_attribute_uri(
    attr_type_sampler, columns
)

l = []
for ith, a in os.iterrows():
    l.append(dict(a))
    ...
