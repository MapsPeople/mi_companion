from integration_system.mi import get_remote_solution
from integration_system.tools.serialisation import collection_to_df

a = get_remote_solution("kemper-merged")
shape_df = collection_to_df(a.location_types, pop_keys=["display_rule"])

l = []
for ith, a in shape_df.iterrows():
    l.append(dict(a))
    ...
