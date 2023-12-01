import geopandas
import shapely
from jord.qlive_utilities import add_shapely_layer, add_dataframe_layer


def add_cms_layer_hierarchy(qgis_instance_handle, solution, venues_map, solution_name):
    venue = None
    for v in solution.venues:
        if v.external_id == venues_map[solution_name]:
            venue = v
            break

    add_shapely_layer(
        qgis_instance_handle=qgis_instance_handle,
        geoms=[venue.polygon],
        name="venue",
    )

    d = solution.doors.to_df(index_key="external_id")
    if not d.empty:
        door_df = geopandas.GeoDataFrame(d.T, geometry="linestring")

        add_dataframe_layer(
            qgis_instance_handle=qgis_instance_handle,
            dataframe=door_df,
            geometry_column="linestring",
            name="doors",
        )

    building_df = geopandas.GeoDataFrame(
        solution.buildings.to_df(index_key="external_id").T[
            ["external_id", "name", "polygon"]
        ],
        geometry="polygon",
    )

    add_dataframe_layer(
        qgis_instance_handle=qgis_instance_handle,
        dataframe=building_df,
        geometry_column="polygon",
        name="buildings",
    )

    f = solution.floors.to_df(index_key="external_id").T
    if not f.empty:
        floors_df = geopandas.GeoDataFrame(
            f[["external_id", "name", "polygon"]], geometry="polygon"
        )

        add_dataframe_layer(
            qgis_instance_handle=qgis_instance_handle,
            dataframe=floors_df,
            geometry_column="polygon",
            name="floors",
        )

    r = solution.rooms.to_df(index_key="external_id").T
    if not r.empty:
        # r.loc[:, r.columns != "polygon"] = r.loc[:, r.columns != "polygon"].astype(            str        )  # MUST CAST
        # TODO: FLATTEN DICTS!
        rooms_df = geopandas.GeoDataFrame(
            r[["external_id", "name", "polygon"]], geometry="polygon"
        )

        add_dataframe_layer(
            qgis_instance_handle=qgis_instance_handle,
            dataframe=rooms_df,
            geometry_column="polygon",
            name="rooms",
        )

    a = solution.areas.to_df()
    if not a.empty:
        areas_df = geopandas.GeoDataFrame(a, geometry="polygon")

        add_dataframe_layer(
            qgis_instance_handle=qgis_instance_handle,
            dataframe=areas_df,
            geometry_column="polygon",
            name="areas",
        )

    p = solution.points_of_interest.to_df()
    if not p.empty:
        poi_df = geopandas.GeoDataFrame(p, geometry="point")

        add_dataframe_layer(
            qgis_instance_handle=qgis_instance_handle,
            dataframe=poi_df,
            geometry_column="point",
            name="pois",
        )
