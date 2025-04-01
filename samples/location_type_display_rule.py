from integration_system.mi import get_remote_solution
from integration_system.pandas_serde import collection_to_df

a = get_remote_solution("kemper-merged")
shape_df = collection_to_df(a.location_types)

l = []
for ith, a in shape_df.iterrows():
    l.append(dict(a))
    ...
