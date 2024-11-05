"""Tests for QGIS functionality.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = "tim@linfiniti.com"
__date__ = "20/01/2011"
__copyright__ = "Copyright 2012, Australia Indonesia Facility for " "Disaster Reduction"

import unittest


class QGISTest(unittest.TestCase):
    """Test the QGIS Environment"""

    def test_qgis_environment(self) -> None:
        from .utilities import get_qgis_app

        get_qgis_app()

        # noinspection PyUnresolvedReferences
        from qgis.core import QgsProviderRegistry

        """QGIS environment has the expected providers"""

        r = QgsProviderRegistry.instance()
        self.assertIn("gdal", r.providerList())
        self.assertIn("ogr", r.providerList())


if __name__ == "__main__":
    unittest.main()
