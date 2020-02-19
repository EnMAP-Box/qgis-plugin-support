# coding=utf-8
"""Resources test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'benjamin.jakimow@geo.hu-berlin.de'
__date__ = '2017-07-17'
__copyright__ = 'Copyright 2017, Benjamin Jakimow'

import unittest, pickle, os
import xml.etree.ElementTree as ET
from qgis import *
from qgis.core import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.Qt import *
from qgis.PyQt.QtCore import *
from osgeo import gdal, ogr, osr
from qps.testing import TestObjects

from qps.utils import *
from qps.testing import TestCase

class TestUtils(TestCase):
    def setUp(self):
        super().setUp()

        self.wmsUri = r'crs=EPSG:3857&format&type=xyz&url=https://mt1.google.com/vt/lyrs%3Ds%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=19&zmin=0'
        self.wfsUri = r'restrictToRequestBBOX=''1'' srsname=''EPSG:25833'' typename=''fis:re_postleit'' url=''http://fbinter.stadt-berlin.de/fb/wfs/geometry/senstadt/re_postleit'' version=''auto'''

    def tearDown(self):


        super().tearDown()

    def test_loadUi(self):

        import qps
        sources = list(file_search(dn(qps.__file__), '*.ui', recursive=True))
        sources = [s for s in sources if not 'pyqtgraph' in s]
        for pathUi in sources:
            tree = ET.parse(pathUi)
            root = tree.getroot()
            self.assertEqual(root.tag, 'ui')
            baseClass = root.find('widget').attrib['class']

            print('Try to load {} as {}'.format(pathUi, baseClass))
            self.assertIsInstance(baseClass, str)

            if baseClass == 'QDialog':
                class TestWidget(QDialog):

                    def __init__(self):
                        super().__init__()
                        loadUi(pathUi, self)

            elif baseClass == 'QWidget':
                class TestWidget(QWidget):

                    def __init__(self):
                        super().__init__()
                        loadUi(pathUi, self)

            elif baseClass == 'QMainWindow':
                class TestWidget(QMainWindow):

                    def __init__(self):
                        super().__init__()
                        loadUi(pathUi, self)
            elif baseClass == 'QDockWidget':
                class TestWidget(QDockWidget):
                    def __init__(self):
                        super().__init__()
                        loadUi(pathUi, self)
            else:
                warnings.warn('BaseClass {} not implemented\nto test {}'.format(baseClass, pathUi), Warning)
                continue


            w = None
            try:
                w = TestWidget()
                s = ""

            except Exception as ex:
                info = 'Failed to load {}'.format(pathUi)
                info += '\n' + str(ex)
                self.fail(info)


    def test_gdal_filesize(self):

        DIR_VRT_STACK = r'Q:\Processing_BJ\99_OSARIS_Testdata\Loibl-2019-OSARIS-Ala-Archa\BJ_VRT_Stacks'

        if os.path.isdir(DIR_VRT_STACK):
            for path in file_search(DIR_VRT_STACK, '*.vrt'):
                size = gdalFileSize(path)
                self.assertTrue(size > 0)


    def test_file_search(self):


        rootQps = pathlib.Path(__file__).parents[1]
        self.assertTrue(rootQps.is_dir())

        results = list(file_search(rootQps, 'test_utils.py', recursive=False))
        self.assertIsInstance(results, list)
        self.assertTrue(len(results) == 0)

        for pattern in ['test_utils.py', 'test_utils*.py', re.compile(r'test_utils\.py')]:

            results = list(file_search(rootQps, pattern, recursive=True))
            self.assertIsInstance(results, list)
            self.assertTrue(len(results) == 1)
            self.assertTrue(os.path.isfile(results[0]))

        results = list(file_search(rootQps, 'speclib', directories=True, recursive=True))
        self.assertIsInstance(results, list)
        self.assertTrue(len(results) == 1)
        self.assertTrue(os.path.isdir(results[0]))


    def test_vsimem(self):

        from qps.utils import check_vsimem

        b = check_vsimem()
        self.assertIsInstance(b, bool)


    def test_spatialObjects(self):

        pt1 = SpatialPoint('EPSG:4326', 300,300)
        self.assertIsInstance(pt1, SpatialPoint)
        d = pickle.dumps(pt1)
        pt2 = pickle.loads(d)


        self.assertEqual(pt1, pt2)


    def test_gdalDataset(self):

        ds = TestObjects.createRasterDataset()
        path = ds.GetDescription()
        ds1 = gdalDataset(path)
        self.assertIsInstance(ds1, gdal.Dataset)
        ds2 = gdalDataset(ds1)
        self.assertEqual(ds1, ds2)


    def test_bandNames(self):

        ds = TestObjects.createRasterDataset()
        pathRaster = ds.GetDescription()

        validSources = [QgsRasterLayer(self.wmsUri, '', 'wms'),
                        pathRaster,
                        QgsRasterLayer(pathRaster),
                        gdal.Open(pathRaster)]

        for src in validSources:
            names = displayBandNames(src, leadingBandNumber=True)
            self.assertIsInstance(names, list, msg='Unable to derive band names from {}'.format(src))
            self.assertTrue(len(names) > 0)


    def test_coordinateTransformations(self):

        ds = TestObjects.createRasterDataset(300, 500)
        lyr = QgsRasterLayer(ds.GetDescription())

        self.assertEqual(ds.GetGeoTransform(), layerGeoTransform(lyr))

        self.assertIsInstance(ds, gdal.Dataset)
        self.assertIsInstance(lyr, QgsRasterLayer)
        gt = ds.GetGeoTransform()
        crs = QgsCoordinateReferenceSystem(ds.GetProjection())

        self.assertTrue(crs.isValid())

        geoCoordinateUL = QgsPointXY(gt[0], gt[3])
        shiftToCenter = QgsVector(gt[1]*0.5, gt[5]*0.5)
        geoCoordinateCenter = geoCoordinateUL + shiftToCenter
        pxCoordinate = geo2px(geoCoordinateUL, gt)
        pxCoordinate2 = geo2px(geoCoordinateUL, lyr)
        self.assertEqual(pxCoordinate.x(), 0)
        self.assertEqual(pxCoordinate.y(), 0)
        self.assertAlmostEqual(px2geo(pxCoordinate, gt), geoCoordinateCenter)

        self.assertEqual(pxCoordinate, pxCoordinate2)

        spatialPoint = SpatialPoint(crs, geoCoordinateUL)
        pxCoordinate = geo2px(spatialPoint, gt)
        self.assertEqual(pxCoordinate.x(), 0)
        self.assertEqual(pxCoordinate.y(), 0)
        self.assertAlmostEqual(px2geo(pxCoordinate, gt), geoCoordinateUL + shiftToCenter)


    def test_createQgsField(self):

        values = [1, 2.3, 'text',
                  np.int8(1),
                  np.int16(1),
                  np.int32(1),
                  np.int64(1),
                  np.uint8(1),
                  np.uint(1),
                  np.uint16(1),
                  np.uint32(1),
                  np.uint64(1),
                  np.float(1),
                  np.float16(1),
                  np.float32(1),
                  np.float64(1),
                  ]

        for v in values:
            print('Create QgsField for {}'.format(type(v)))
            field = createQgsField('field', v)
            self.assertIsInstance(field, QgsField)

    def test_convertMetricUnits(self):

        print('DONE', flush=True)
        self.assertEqual(convertMetricUnit(100, 'm', 'km'), 0.1)
        self.assertEqual(convertMetricUnit(0.1, 'km', 'm'), 100)

        self.assertEqual(convertMetricUnit(400, 'nm', 'μm'), 0.4)
        self.assertEqual(convertMetricUnit(0.4, 'μm', 'nm'), 400)

        self.assertEqual(convertMetricUnit(400, 'nm', 'km'), 4e-10)


    def test_appendItemsToMenu(self):
        B = QMenu()

        action = B.addAction('Do something')
        menuA = QMenu()
        appendItemsToMenu(menuA, B)

        self.assertTrue(action in menuA.children())


    def test_value2string(self):

        valueSet = [[1,2,3],
                        1,
                        '',
                        None,
                        np.zeros((3,3,))
                        ]

        for i, values in enumerate(valueSet):
            print('Test {}:{}'.format(i+1, values))
            s = value2str(values, delimiter=';')
            self.assertIsInstance(s, str)

    def test_savefilepath(self):

        valueSet = ['dsdsds.png',
                    'foo\\\\\\?<>bar',
                    None,
                    r"_bound method TimeSeriesDatum.date of TimeSeriesDatum(2014-01-15,_class 'timeseriesviewer.timeseries.SensorInstrument'_ LS)_.Map View 1.png"
                    ]

        for i, text in enumerate(valueSet):
            s = filenameFromString(text)
            print('Test {}:"{}"->"{}"'.format(i + 1, text, s))
            self.assertIsInstance(s, str)

    def test_selectMapLayersDialog(self):

        lyrR = TestObjects.createRasterLayer()
        lyrV = TestObjects.createVectorLayer()
        QgsProject.instance().addMapLayers([lyrR, lyrV])
        d = SelectMapLayersDialog()
        d.addLayerDescription('Any Type', QgsMapLayerProxyModel.All)
        layers = d.mapLayers()
        self.assertIsInstance(layers, list)
        self.assertTrue(len(layers) == 1)
        self.assertListEqual(layers, [lyrR])

        d.addLayerDescription('A Vector Layer', QgsMapLayerProxyModel.VectorLayer)
        d.addLayerDescription('A Raster Layer', QgsMapLayerProxyModel.RasterLayer)

        self.showGui(d)

    def test_defaultBands(self):

        ds = TestObjects.createRasterDataset(nb=10)
        self.assertIsInstance(ds, gdal.Dataset)

        self.assertListEqual([0, 1, 2], defaultBands(ds))
        self.assertListEqual([0, 1, 2], defaultBands(ds.GetDescription()))

        ds.SetMetadataItem('default bands', '{4,3,1}', 'ENVI')
        self.assertListEqual([4, 3, 1], defaultBands(ds))

        ds.SetMetadataItem('default_bands', '{4,3,1}', 'ENVI')
        self.assertListEqual([4, 3, 1], defaultBands(ds))


    def test_nextColor(self):

        c = QColor('#ff012b')
        for i in range(500):
            c = nextColor(c, mode='con')
            self.assertIsInstance(c, QColor)
            self.assertTrue(c.name() != '#000000')

        c = QColor('black')
        for i in range(500):
            c = nextColor(c, mode='cat')
            self.assertIsInstance(c, QColor)
            self.assertTrue(c.name() != '#000000')


if __name__ == "__main__":
    unittest.main()

