import itertools
import os.path
import re
import unittest
from typing import List

import numpy as np

from osgeo import gdal, ogr, gdal_array
from qgis.PyQt.QtWidgets import QWidget, QPushButton, QHBoxLayout, QVBoxLayout
from qgis.core import QgsFeature
from qgis.core import QgsRasterLayer, QgsVectorLayer, QgsProject, QgsMapLayer
from qgis.gui import QgsMapCanvas, QgsDualView, QgsRasterBandComboBox, QgsMapLayerComboBox
from qps.layerconfigwidgets.gdalmetadata import GDALBandMetadataModel, GDALMetadataItemDialog, GDALMetadataModel, \
    GDALMetadataModelConfigWidget, BandFieldNames, ENVIMetadataUtils
from qps.qgsrasterlayerproperties import QgsRasterLayerSpectralProperties
from qps.testing import TestCase, TestObjects
from qpstestdata import enmap


class ControlWidget(QWidget):

    def __init__(self, *args, **kwds):

        super().__init__(*args, **kwds)
        self.canvas = QgsMapCanvas()
        self.w = GDALMetadataModelConfigWidget(None, self.canvas)
        self.w.setEditable(False)
        self.w.widgetChanged.connect(lambda: print('Changed'))

        self.canvas.setLayers([self.w.mapLayer()])
        self.canvas.mapSettings().setDestinationCrs(self.w.mapLayer().crs())
        self.canvas.zoomToFullExtent()
        self.btnEdit = QPushButton('Edit')
        self.btnEdit.setCheckable(True)
        self.btnEdit.toggled.connect(self.w.setEditable)
        self.btnApply = QPushButton('Apply')
        self.btnApply.clicked.connect(self.w.apply)
        self.btnZoom = QPushButton('Center')
        self.btnZoom.clicked.connect(self.canvas.zoomToFullExtent)
        self.btnReload = QPushButton('Reload')
        self.btnReload.clicked.connect(self.w.syncToLayer)

        cb = QgsRasterBandComboBox()
        cb.setLayer(self.w.mapLayer())

        def onLayerChanged(layer):
            if isinstance(layer, QgsRasterLayer):
                cb.setLayer(layer)
            else:
                cb.setLayer(None)
            self.w.setLayer(layer)

        self.cbChangeLayer = QgsMapLayerComboBox()
        self.cbChangeLayer.layerChanged.connect(onLayerChanged)

        hl1 = QHBoxLayout()
        for widget in [self.btnEdit,
                       self.btnApply,
                       self.btnReload,
                       self.btnZoom,
                       self.cbChangeLayer, cb]:
            hl1.addWidget(widget)
        hl2 = QHBoxLayout()
        hl2.addWidget(self.w)
        hl2.addWidget(self.canvas)
        vl = QVBoxLayout()
        vl.addLayout(hl1)
        vl.addLayout(hl2)
        self.setLayout(vl)


class TestsGdalMetadata(TestCase):

    def test_GDALBandMetadataModel(self):
        from qpstestdata import enmap
        img_path = self.createImageCopy(enmap)
        lyr = QgsRasterLayer(img_path)
        model2 = GDALBandMetadataModel()
        c = QgsMapCanvas()
        view = QgsDualView()
        view.init(model2, c)
        model2.setLayer(lyr)
        model2.syncToLayer()
        model2.startEditing()
        model2.applyToLayer()
        self.showGui(view)

    def test_gdal_envi_header_comments(self):

        path = '/vsimem/test.bin'
        gdal_array.SaveArray(np.ones((3, 1, 1)), path, format='ENVI')
        ds: gdal.Dataset = gdal.Open(path, gdal.GA_Update)
        ds.SetMetadataItem('bbl', """{
        0,
        ; a comment to be excluded. See https://www.l3harrisgeospatial.com/docs/enviheaderfiles.html
        1,
        0}""", 'ENVI')
        ds.FlushCache()
        files = ds.GetFileList()
        del ds

        # print ENVI hdr
        path_hdr = '/vsimem/test.hdr'
        fp = gdal.VSIFOpenL(path_hdr, "rb")
        content: str = gdal.VSIFReadL(1, gdal.VSIStatL(path_hdr).size, fp).decode("utf-8")
        gdal.VSIFCloseL(fp)

        # read BBL
        ds: gdal.Dataset = gdal.Open(path)
        bbl = ds.GetMetadataItem('bbl', 'ENVI')
        print(bbl)

        bbl2 = ds.GetMetadata_Dict('ENVI')['bbl']

    def test_QgsRasterLayer_GDAL_interaction(self):

        def readTextFile(path: str) -> str:
            fp = gdal.VSIFOpenL(path, "rb")
            content: str = gdal.VSIFReadL(1, gdal.VSIStatL(path).size, fp).decode("utf-8")
            gdal.VSIFCloseL(fp)
            return content

        def bandNames(dsrc) -> List[str]:
            if isinstance(dsrc, gdal.Dataset):
                return [dsrc.GetRasterBand(b + 1).GetDescription() for b in range(dsrc.RasterCount)]
            elif isinstance(dsrc, QgsRasterLayer):
                return [dsrc.bandName(b + 1) for b in range(dsrc.bandCount())]

        def setBandNames(dsrc: gdal.Dataset, names: List[str]):
            self.assertIsInstance(dsrc, gdal.Dataset)
            for b, n in enumerate(names):
                dsrc.GetRasterBand(b + 1).SetDescription(n)
            dsrc.FlushCache()

        path = '/vsimem/test.bin'
        ds0 = gdal_array.SaveArray(np.ones((3, 1, 1)), path, format='ENVI')
        path_hdr = [f for f in ds0.GetFileList() if f.endswith('.hdr')][0]

        self.assertIsInstance(ds0, gdal.Dataset)
        self.assertEqual(bandNames(ds0), ['', '', ''])

        lyr = QgsRasterLayer(path)
        self.assertTrue(lyr.isValid())
        self.assertEqual(bandNames(lyr), ['Band 1', 'Band 2', 'Band 3'])

        # 1. Write Band Names and the BBL
        # changing metadata will only be written to ENVI hdr if dataset is opened in update mode!
        ds: gdal.Dataset = gdal.Open(path, gdal.GA_Update)
        setBandNames(ds, ['A', 'B', 'C'])
        ds.SetMetadataItem('bbl', '{0,1,0}', 'ENVI')
        ds.SetMetadataItem('bbl false', '0,1,0', 'ENVI')
        ds.FlushCache()

        # print PAM
        path_pam = [f for f in ds0.GetFileList() if f.endswith('aux.xml')][0]
        content_pam = readTextFile(path_pam)
        print(content_pam)

        ds2: gdal.Dataset = gdal.Open(path, gdal.GA_ReadOnly)

        # Check band names in GDAL PAM
        self.assertEqual(bandNames(ds), ['A', 'B', 'C'])
        self.assertEqual(bandNames(ds2), ['A', 'B', 'C'])
        self.assertEqual(ds.GetMetadataItem('bbl', 'ENVI'), '{0,1,0}')
        self.assertEqual(ds2.GetMetadataItem('bbl', 'ENVI'), '{0,1,0}')

        # the original data set still points on old band names / MD values!
        self.assertEqual(bandNames(ds0), ['', '', ''])

        # same for QgsRasterLayer, which generates default names
        self.assertEqual(bandNames(lyr), ['Band 1', 'Band 2', 'Band 3'])
        # ... neither a .reload, nor a new layer help
        lyr.dataProvider().bandStatistics(1)
        lyr.reload()
        self.assertEqual(bandNames(lyr), ['Band 1', 'Band 2', 'Band 3'])
        self.assertEqual(bandNames(QgsRasterLayer(path)), ['Band 1', 'Band 2', 'Band 3'])

        # but overwriting the PAM helps
        gdal.FileFromMemBuffer(path_pam, '')
        lyr = QgsRasterLayer(path)
        self.assertEqual(bandNames(lyr), ['Band 1: A', 'Band 2: B', 'Band 3: C'])
        properties = QgsRasterLayerSpectralProperties.fromRasterLayer(lyr)
        self.assertEqual(properties.badBands(), [0, 1, 0])
        # self.assertEqual(bandNames(lyr3), ['Band 1', 'Band 2', 'Band 3'])

        # Check ENVI hdr
        content_hdr = readTextFile(path_hdr)
        content_hdr = re.sub(r',\n', ', ', content_hdr)
        content_hdr = re.sub(r'\{\n', r'{', content_hdr)
        print(content_hdr)
        self.assertTrue('band names = {A, B, C}' in content_hdr)
        self.assertTrue('bbl = {0,1,0}' in content_hdr)

    @unittest.skipIf(gdal.VersionInfo() < '3060000', 'Requires GDAL 3.6+')
    def test_modify_metadata(self):
        nb, nl, ns = 5, 2, 2

        path = self.tempDir() / 'test.img'
        path = path.as_posix()

        drv: gdal.Driver = gdal.GetDriverByName('ENVI')
        ds: gdal.Dataset = drv.Create(path, ns, nl, nb, eType=gdal.GDT_Byte)

        for b in range(ds.RasterCount):
            band: gdal.Band = ds.GetRasterBand(b + 1)
            band.Fill(b + 1)
            band.GetStatistics(1, 1)
            band.SetDescription(f'MyBand {b + 1}')
        ds.FlushCache()
        del band
        originalBandNames = [ds.GetRasterBand(b + 1).GetDescription() for b in range(nb)]

        path_hdr: str = [f for f in ds.GetFileList() if f.endswith('.hdr')][0]
        del ds

        def readHeader():
            fp = gdal.VSIFOpenL(path_hdr, "rb")
            hdr: str = gdal.VSIFReadL(1, gdal.VSIStatL(path_hdr).size, fp).decode("utf-8")
            gdal.VSIFCloseL(fp)
            return hdr

        lyr = QgsRasterLayer(path)
        self.assertTrue(lyr.isValid())

        bandModel = GDALBandMetadataModel()
        bandModel.setLayer(lyr)

        map1 = bandModel.asMap()
        # this model is a vector layer with fields for each supported band property
        self.assertIsInstance(bandModel, QgsVectorLayer)

        for feature in bandModel.getFeatures():
            feature: QgsFeature
            fid = feature.id()
            self.assertTrue(0 < fid <= nb)
            self.assertEqual(originalBandNames[fid - 1], feature.attribute(BandFieldNames.Name))

        modifiedBandNames = ['A', 'B', 'C', 'D', 'E']
        # modify band properties
        # set a band names
        bandModel.startEditing()

        for b, name in enumerate(modifiedBandNames):
            f: QgsFeature = bandModel.getFeature(b + 1)
            f.setAttribute(BandFieldNames.Name, name)
            bandModel.updateFeature(f)

            # bandModel.changeAttributeValue(3, iField, 'Another Band Name')

        bandModel.mMapLayer.reload()
        bandModel.applyToLayer()

        ds2: gdal.Dataset = gdal.Open(path)
        bandNames = [ds2.GetRasterBand(b + 1).GetDescription() for b in range(ds2.RasterCount)]

        self.assertListEqual(bandNames, modifiedBandNames)

        # hdr2 = readHeader()
        # bandModel.commitChanges()
        # self.assertTrue('My Band Name' not in hdr1)
        # self.assertTrue('My Band Name' in hdr2)

    def test_ENVI_Header_Utils(self):

        hdr = """
ENVI
foo A=bar 
foo B = bar2 
foo C=b a r 3 
foo D={a,b, c}
foo E={1,2
,3,4}
stupid -- broken 
 stuff
foo F = {1, 2
    , 3, 4
    }
foo G = {1,
  # comment
2}
foo H =
        """
        found = ENVIMetadataUtils.parseEnviHeader(hdr)
        for a in 'ABCDEFG':
            k = f'foo {a}'
            self.assertTrue(k in found.keys())
            v = found[k]
            self.assertIsInstance(v, (str, list))
        for a in 'H':
            self.assertTrue(f'foo {a}' not in found.keys())


    def test_GDAL_PAM(self):
        test_dir = self.createTestOutputDirectory(subdir='gdalmetadata_PAM')
        path = test_dir / 'example.tif'
        ds: gdal.Dataset = gdal.Translate(path.as_posix(), enmap)
        del ds

        lyr = QgsRasterLayer(path.as_posix())
        lyr2 = lyr.clone()
        self.assertTrue(lyr.isValid())
        ds: gdal.Dataset = gdal.Open(path.as_posix(), gdal.GA_Update)
        self.assertIsInstance(ds, gdal.Dataset)
        ds.SetMetadataItem('Example', 'foobar', 'MyDomain')
        band = ds.GetRasterBand(1)
        band.SetDescription('BAND_EXAMPLE')
        ds.FlushCache()
        del ds

    def test_GDALMetadataModelConfigWidget(self):
        from qpstestdata import envi_bsq, enmap_polygon

        envi_bsq = self.createImageCopy(envi_bsq)

        lyrR = QgsRasterLayer(envi_bsq, 'ENVI')
        lyrV = QgsVectorLayer(enmap_polygon, 'Vector')

        layers = [QgsRasterLayer(enmap, 'EnMAP'),
                  lyrR,
                  lyrV,
                  TestObjects.createRasterLayer(),
                  TestObjects.createSpectralLibrary(),
                  TestObjects.createSpectralLibrary(),
                  TestObjects.createRasterLayer(nc=3)]

        QgsProject.instance().addMapLayers(layers)

        W = ControlWidget()
        self.showGui(W)

    def test_rasterFormats(self):
        from qpstestdata import enmap
        properties = QgsRasterLayerSpectralProperties.fromRasterLayer(enmap)
        wl = properties.wavelengths()
        wlu = properties.wavelengthUnits()
        bbl = properties.badBands()
        fwhm = properties.fwhm()
        fwhm = [0.042 if n % 2 == 0 else 0.024 for n in range(len(fwhm))]
        files = []

        test_dir = self.createTestOutputDirectory(subdir='gdalmetadata')

        def create_vrt(name: str) -> gdal.Dataset:
            path = (test_dir / f'{name}.vrt').as_posix()
            assert path not in files, 'already created'
            files.append(path)
            ds = gdal.Translate(path, enmap)
            # clear existing metadata
            ds.SetMetadataItem('wavelength', None)
            ds.SetMetadataItem('wavelength_units', None)
            assert isinstance(ds, gdal.Dataset)
            return ds

        def set_metadata(ds: gdal.Dataset,
                         key: str,
                         values: list,
                         domain: str = None,
                         band_wise: bool = True):
            assert ds.RasterCount == len(values)
            if band_wise:
                for b in range(ds.RasterCount):
                    band: gdal.Band = ds.GetRasterBand(b + 1)
                    band.SetMetadataItem(key, str(values[b]), domain)
            else:
                value_string = '{' + ','.join([str(v) for v in values]) + '}'
                ds.SetMetadataItem(key, value_string, domain)

            ds.FlushCache()

        domains = [None, 'ENVI']
        band_wise = [False, True]

        for domain, bw in itertools.product(domains, band_wise):
            suffix = ''
            if domain:
                suffix += f'_{domain}'
            if bw:
                suffix += '_bandwise'
            else:
                suffix += '_dataset'
            kwds = dict(domain=domain, band_wise=bw)
            ds = create_vrt('all' + suffix)
            set_metadata(ds, 'wavelength', wl, **kwds)
            set_metadata(ds, 'wavelength_units', wlu, **kwds)
            set_metadata(ds, 'bbl', bbl, **kwds)
            set_metadata(ds, 'fwhm', fwhm, **kwds)

            ds = create_vrt('wl_only' + suffix)
            set_metadata(ds, 'wavelength', wl, **kwds)

            ds = create_vrt('wl_and_wlu' + suffix)
            set_metadata(ds, 'wavelength', wl, **kwds)
            set_metadata(ds, 'wavelength_units', wlu, **kwds)

            ds = create_vrt('wlu_only' + suffix)
            set_metadata(ds, 'wavelength_units', wlu, **kwds)

        ds = create_vrt('plain')
        files.append(enmap)

        layers = []
        for file in files:
            lyr = QgsRasterLayer(file, os.path.basename(file))
            self.assertTrue(lyr.isValid())
            layers.append(lyr)
        QgsProject.instance().addMapLayers(layers)

        w = ControlWidget()
        self.showGui(w)

    def test_GDALMetadataModel(self):

        layers = [QgsRasterLayer(self.createImageCopy(enmap)),
                  TestObjects.createRasterLayer(),
                  TestObjects.createVectorLayer(),
                  TestObjects.createSpectralLibrary()
                  ]
        for lyr in layers:
            self.assertIsInstance(lyr, QgsMapLayer)
            model = GDALMetadataModel()
            model.setLayer(lyr)
            model.startEditing()
            model.syncToLayer()
            model.applyToLayer()

    def test_GDALMetadataModelItemWidget(self):

        majorObjects = [gdal.Dataset.__name__,
                        f'{gdal.Band.__name__}_1',
                        ogr.DataSource.__name__,
                        f'{ogr.Layer.__name__}_1',
                        f'{ogr.Layer.__name__}_layername',
                        ]
        domains = ['Domains 1', 'domains2']
        d = GDALMetadataItemDialog(major_objects=majorObjects,
                                   domains=domains)
        d.setKey('MyKey')
        d.setValue('MyValue')
        d.setDomain('MyDomain')
        for mo in majorObjects:
            self.assertTrue(d.setMajorObject(mo))

        self.showGui(d)


if __name__ == "__main__":
    unittest.main(buffer=False)
