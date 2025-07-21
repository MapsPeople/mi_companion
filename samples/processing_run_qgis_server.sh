#!/usr/sh


echo "{'inputs': {'INPUT': 'my_shape.shp', 'DISTANCE': 5}}" | qgis_process run native:buffer -


# Convert map to raster   {'EXTENT': '1099209.186700000,1118012.480000000,7761059.304200000,7775553.509500000 '
 #'[EPSG:3857]',
 #'EXTENT_BUFFER': 0.0,
 #'LAYERS': None,
 #'MAKE_BACKGROUND_TRANSPARENT': False,
 #'MAP_THEME': None,
 #'MAP_UNITS_PER_PIXEL': 100.0,
 #'OUTPUT': <QgsProcessingOutputLayerDefinition {'sink':/home/heider/Downloads/sd/sd.tif, 'createOptions': {}}>,
 #'TILE_SIZE': 1024}





#   Generate XYZ tiles (MBTiles)    { 'BACKGROUND_COLOR' : QColor(0, 0, 0, 0), 'DPI' : 96, 'EXTENT' : '1098817.451500000,1114095.127300000,7763409.715900000,7776728.715300000 [EPSG:3857]', 'METATILESIZE' : 4, 'OUTPUT_FILE' : 'TEMPORARY_OUTPUT', 'QUALITY' : 75, 'TILE_FORMAT' : 0, 'ZOOM_MAX' : 12, 'ZOOM_MIN' : 12 }
