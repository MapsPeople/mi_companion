# noinspection PyUnresolvedReferences
import qgis

# noinspection PyUnresolvedReferences
from qgis.core import QgsEditorWidgetSetup

from jord.qgis_utilities.helpers.widgets import COLOR_WIDGET, make_range_widget

try:
    from enum import StrEnum
except ImportError:
    from strenum import StrEnum

BOOLEAN_LOCATION_FIELDS = (
    "is_searchable",
    "is_active",
    # "is_obstacle",
    # "is_selectable"
    "display_rule.model3d.visible",
    "display_rule.model2d.visible",
)

STR_LOCATION_FIELDS = (
    "external_id",
    "translations.en.name",
    "display_rule.model3d.model",
    "admin_id",
)

RANGE_WIDGET_360_WIDGET = make_range_widget()
RANGE_WIDGET_01_WIDGET = make_range_widget(0, 1, 0.1)


RANGE_LOCATION_FIELDS = {
    "display_rule.model3d.rotation_x": RANGE_WIDGET_360_WIDGET,
    "display_rule.model3d.rotation_y": RANGE_WIDGET_360_WIDGET,
    "display_rule.model3d.rotation_z": RANGE_WIDGET_360_WIDGET,
    "street_view_config.pov_heading": make_range_widget(-90, 90),
    "street_view_config.pov_pitch": make_range_widget(-180, 180),
    "display_rule.model2d.bearing": RANGE_WIDGET_360_WIDGET,
    "display_rule.polygon.fill_opacity": RANGE_WIDGET_01_WIDGET,
    "display_rule.polygon.stroke_opacity": RANGE_WIDGET_01_WIDGET,
    "display_rule.label_style.text_opacity": RANGE_WIDGET_01_WIDGET,
}

COLOR_LOCATION_FIELDS = (
    "display_rule.polygon.stroke_color",
    "display_rule.polygon.fill_color",
    "display_rule.extrusion.color"
    "display_rule.walls.color"
    "display_rule.label_style.halo_color"
    "display_rule.label_style.text_color",
)


NOT_NULL_FIELDS = (  # MARK all tranlation names as required "not_null"
    "translations.en.name",
    "location_type",
    "is_searchable",
    "is_active",
)

REUSE_LAST_FIELDS = (
    "translations.en.name",
    "location_type",
    "is_searchable",
    "is_active",
    "is_selectable",
    "is_obstacle",
)

FLOAT_LOCATION_FIELDS = (
    "settings_3d_width",
    "settings_3d_margin",
    "display_rule.model3d.scale",
    # "display_rule.label_zoom_from",
    # "display_rule.label_zoom_to",
    *RANGE_LOCATION_FIELDS.keys(),
)
INT_LOCATION_FIELDS = (
    # "display_rule.label_zoom_from",
    # "display_rule.label_zoom_to",
)
DATETIME_LOCATION_FIELDS = ("active_from", "active_to")

LIST_LOCATION_TYPE_FIELDS = ("restrictions", "category_keys", "details")


class LocationGeometryType(StrEnum):
    point = "point"
    # linestring = "linestring"
    polygon = "polygon"


BOOLEAN_LOCATION_TYPE_ATTRS = (
    # "is_obstacle",
    # "is_selectable",
    "display_rule.model3d.visible",
    "display_rule.model2d.visible",
)
STR_LOCATION_TYPE_ATTRS = (
    "translations.en.name",
    "display_rule.model3d.model",
    "admin_id",
    "color",
)
RANGE_LOCATION_ATTRS = {
    "display_rule.model3d.rotation_x": make_range_widget(),
    "display_rule.model3d.rotation_y": make_range_widget(),
    "display_rule.model3d.rotation_z": make_range_widget(),
    "display_rule.model2d.bearing": make_range_widget(),
    "display_rule.polygon.fill_opacity": make_range_widget(0, 1, 0.1),
    "display_rule.polygon.stroke_opacity": make_range_widget(0, 1, 0.1),
    "display_rule.label_style.text_opacity": make_range_widget(0, 1, 0.1),
}
COLOR_LOCATION_ATTRS = (
    "color" "display_rule.polygon.stroke_color",
    "display_rule.polygon.fill_color",
    "display_rule.extrusion.color"
    "display_rule.walls.color"
    "display_rule.label_style.halo_color"
    "display_rule.label_style.text_color",
)
RGB_COLOR_PICKER = COLOR_WIDGET
FLOAT_LOCATION_TYPE_ATTRS = (
    "settings_3d_margin",
    "settings_3d_width",
    *RANGE_LOCATION_ATTRS.keys(),
    # "display_rule.label_zoom_from",
    # "display_rule.label_zoom_to",
)
INTEGER_LOCATION_TYPE_ATTRS = (
    # "display_rule.label_zoom_from",
    # "display_rule.label_zoom_to",
)
LIST_LOCATION_TYPE_ATTRS = ("restrictions",)
