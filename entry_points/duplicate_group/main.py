#!/usr/bin/python


def run(*, iface, appendix: str = " (Copy)") -> None:
    from jord.qgis_utilities.helpers import duplicate_groups

    duplicate_groups(iface.activeLayer(), appendix)
