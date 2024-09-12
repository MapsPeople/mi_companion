from PyQt5.QtGui import QTransform


def read_wld_file(geom, wld_file_path):
    assert wld_file_path is not None
    assert wld_file_path.exists()
    with open(wld_file_path) as wld_file:
        m32 = (float(c) for c in wld_file.readlines())

        transformer = QTransform(*m32)

        geom.transform(transformer)
