# coding=utf-8
"""Resources test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 3 of the License, or
     (at your option) any later version.

"""

__author__ = 'benjamin.jakimow@geo.hu-berlin.de'

import unittest, time
from qgis.core import *
from qgis.gui import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from osgeo import gdal, ogr, osr
from qps.testing import initQgisApplication, TestObjects
from qps.layerproperties import *
QGIS_APP = initQgisApplication()

SHOW_GUI = True and os.environ.get('CI') is None

LAYER_WIDGET_REPS = 5 if os.environ.get('CI') is None else 5

class LayerRendererTests(unittest.TestCase):


    def test_subLayerDefinitions(self):


        from qpstestdata import testvectordata, landcover, enmap
        from qps.layerproperties import subLayers, subLayerDefinitions

        p = enmap
        sDefs = subLayers(QgsRasterLayer(p))
        self.assertIsInstance(sDefs, list)
        self.assertTrue(len(sDefs) == 1)

        vl = QgsVectorLayer(testvectordata)
        sLayers = subLayers(vl)
        self.assertIsInstance(sLayers, list)
        self.assertTrue(len(sLayers) == 2)

        p = r'F:\Temp\Hajo\S3A_OL_2_EFR____20160614T082507_20160614T082707_20170930T190837_0119_005_178______MR1_R_NT_002_vical_c2rcc015nets20170704.nc'

        if os.path.isfile(p):
            rl = QgsRasterLayer(p)
            sDefs = subLayerDefinitions(rl)
            self.assertTrue(sDefs, list)
            self.assertTrue(len(sDefs) > 0)
            
            sLayers = subLayers(rl)

            self.assertTrue(sLayers, list)
            self.assertTrue(len(sLayers) > 0)



    def test_defaultRenderer(self):

        #1 band, byte
        ds = TestObjects.inMemoryImage(nb=1, eType=gdal.GDT_Byte)
        lyr = QgsRasterLayer(ds.GetDescription())
        r = defaultRasterRenderer(lyr)
        self.assertIsInstance(r, QgsSingleBandGrayRenderer)

        # 1 band, classification
        ds = TestObjects.inMemoryImage(nc=3)
        lyr = QgsRasterLayer(ds.GetDescription())
        r = defaultRasterRenderer(lyr)
        self.assertIsInstance(r, QgsPalettedRasterRenderer)

        # 3 bands, byte
        ds = TestObjects.inMemoryImage(nb=3, eType=gdal.GDT_Byte)
        lyr = QgsRasterLayer(ds.GetDescription())
        r = defaultRasterRenderer(lyr)
        self.assertIsInstance(r, QgsMultiBandColorRenderer)

        # 10 bands, int
        ds = TestObjects.inMemoryImage(nb=10, eType=gdal.GDT_Int16)
        lyr = QgsRasterLayer(ds.GetDescription())
        r = defaultRasterRenderer(lyr)
        self.assertIsInstance(r, QgsMultiBandColorRenderer)

    def test_QgsMapLayerConfigWidget(self):

        lyr = TestObjects.createRasterLayer(nb=3)
        QgsProject.instance().addMapLayer(lyr)
        canvas = QgsMapCanvas()
        canvas.setLayers([lyr])
        canvas.setExtent(canvas.fullExtent())

        w1 = QgsRendererRasterPropertiesWidget(lyr, canvas, None)
        w1.show()


        if SHOW_GUI:
            QGIS_APP.exec_()

    def test_rasterLayerPropertiesWidget(self):

        lyr = TestObjects.createRasterLayer(nb=3)
        QgsProject.instance().addMapLayer(lyr)
        canvas = QgsMapCanvas()
        canvas.setLayers([lyr])
        canvas.setExtent(canvas.fullExtent())
        w = RasterLayerProperties(lyr, canvas)
        self.assertIsInstance(w, RasterLayerProperties)

        if SHOW_GUI:
            canvas.show()
            w.show()
            QGIS_APP.exec_()

    def test_rasterLayerPropertiesWidgetRepeated(self):

        lyr = TestObjects.createRasterLayer(nb=3)
        QgsProject.instance().addMapLayer(lyr)
        canvas = QgsMapCanvas()
        canvas.setLayers([lyr])
        canvas.setExtent(canvas.fullExtent())
        for i in range(LAYER_WIDGET_REPS):
            print('open {}'.format(i))
            w = RasterLayerProperties(lyr, canvas)
            self.assertIsInstance(w, RasterLayerProperties)
            w.show()
            QApplication.processEvents()


        print('Done')

    def test_vectorLayerPropertiesWidgetRepeated(self):

        lyr = TestObjects.createVectorLayer()

        import qps
        qps.registerEditorWidgets()
        w = VectorLayerProperties(lyr, None)
        self.assertIsInstance(w, VectorLayerProperties)
        canvas = QgsMapCanvas()
        canvas.setLayers([lyr])
        canvas.setExtent(canvas.fullExtent())

        for i in range(LAYER_WIDGET_REPS):
            print('open {}'.format(i))
            w = VectorLayerProperties(lyr, canvas)
            self.assertIsInstance(w, VectorLayerProperties)
            w.show()
            QApplication.processEvents()
            # time.sleep(1)

        print('Done')


    def test_vectorLayerPropertiesWidget(self):

        lyr = TestObjects.createVectorLayer()

        import qps
        qps.registerEditorWidgets()
        w = VectorLayerProperties(lyr, None)
        self.assertIsInstance(w, VectorLayerProperties)

        if SHOW_GUI:
            w.show()
            QGIS_APP.exec_()




if __name__ == "__main__":
    unittest.main()



QGIS_APP.quit()