import processing

processing.run(
    "native:buffer",
    {
        "INPUT": "memory://Polygon?crs=EPSG:4326&field=external_id:string(255,0)&field=name:string(255,0)&uid={7114a0c0-3555-485e-946f-eb470aca43cb}",
        "DISTANCE": 10,
        "SEGMENTS": 5,
        "END_CAP_STYLE": 0,
        "JOIN_STYLE": 0,
        "MITER_LIMIT": 2,
        "DISSOLVE": False,
        "OUTPUT": "TEMPORARY_OUTPUT",
    },
)
