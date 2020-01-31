# -*- coding: utf-8 -*-

"""
***************************************************************************

    ---------------------
    Date                 : 30.11.2017
    Copyright            : (C) 2017 by Benjamin Jakimow
    Email                : benjamin jakimow at geo dot hu-berlin dot de
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""
# noinspection PyPep8Naming
import unittest, tempfile, shutil
from qgis.core import *
from qgis.gui import *
from qps.testing import TestObjects, TestCase


from qpstestdata import enmap, hymap
from qpstestdata import speclib as speclibpath


import qps
import qps.speclib

from qps.speclib.csvdata import *
from qps.speclib.envi import *
from qps.speclib.asd import *
from qps.speclib.plotting import *


os.environ['CI'] = 'True'

TEST_DIR = os.path.join(os.path.dirname(__file__), 'SPECLIB_TEST_DIR')

def createLargeSpeclib(n:int=1000)->SpectralLibrary:
    """
    Create a large SpectralLibrary with n Profiles
    """
    from qpstestdata import speclib as pathSpeclib

    speclib = SpectralLibrary()
    assert speclib.startEditing()
    if True:
        profiles = []
        for i in range(1, n+1):
            p = SpectralProfile(fields=speclib.fields())
            xvalues = np.arange(100)
            yvalues = np.ones(100) * i
            p.setValues(xvalues, yvalues)
            profiles.append(p)
        speclib.addProfiles(profiles, addMissingFields=False)
    else:
        nMissing = n
        masterProfiles = SpectralLibrary.readFrom(pathSpeclib, progressDialog=self.progressDialog)[:]
        while nMissing > 0:
            n2 = min(nMissing, len(masterProfiles))
            profiles = masterProfiles[0:n2]
            speclib.addProfiles(profiles)
            assert speclib.commitChanges()
            assert speclib.startEditing()
            nMissing = n - len(speclib)

    assert speclib.commitChanges()
    return speclib


def createSpeclib()->SpectralLibrary:


    # for dx in range(-120, 120, 90):
    #    for dy in range(-120, 120, 90):
    #        pos.append(SpatialPoint(ext.crs(), center.x() + dx, center.y() + dy))

    SLIB = SpectralLibrary()
    assert SLIB.isValid()
    p1 = SpectralProfile()
    p1.setName('No Geometry')

    p1.setValues(x=[0.2, 0.3, 0.2, 0.5, 0.7], y=[1, 2, 3, 4, 5], xUnit='um')
    p2 = SpectralProfile()
    p2.setName('No Geom & NoData')

    p3 = SpectralProfile()
    p3.setValues(x=[250., 251., 253., 254., 256.], y=[0.2, 0.3, 0.2, 0.5, 0.7])
    p3.setXUnit('nm')
    p3.setYUnit('Reflectance')

    p4 = SpectralProfile()
    p4.setValues(x=[0.250, 0.251, 0.253, 0.254, 0.256], y=[0.22, 0.333, 0.222, 0.555, 0.777])
    p4.setXUnit('um')

    ds = TestObjects.createRasterDataset(300, 400, 255)
    path = ds.GetDescription()
    ext = SpatialExtent.fromRasterSource(path)
    posA = ext.spatialCenter()
    posB = SpatialPoint(posA.crs(), posA.x() + 60, posA.y() + 90)

    p5 = SpectralProfile.fromRasterSource(path, posA)
    p5.setName('Position A')
    p6 = SpectralProfile.fromRasterSource(path, posB)
    p6.setName('Position B')

    SLIB.startEditing()
    SLIB.addProfiles([p1, p2, p3, p4, p5, p6])
    SLIB.commitChanges()
    return SLIB

class TestPlotting(TestCase):


    def test_PyQtGraphPlot(self):
        import qps.externals.pyqtgraph as pg
        pg.systemInfo()

        plotWidget = pg.plot(title="Three plot curves")

        item1 = pg.PlotItem(x=[1,2,3],   y=[2, 3, 4], color='white')
        plotWidget.plotItem.addItem(item1)
        self.assertIsInstance(plotWidget, pg.PlotWidget)

        self.showGui(plotWidget)

    def test_SpectralLibraryPlotWidgetSimple(self):

        speclib = createSpeclib()
        w = SpectralLibraryPlotWidget()
        w.setSpeclib(speclib)

        self.showGui(w)

    def test_SpectralLibraryWidgetThousands(self):

        import qpstestdata

        pathSL = os.path.join(os.path.dirname(qpstestdata.__file__), 'roberts2017_urban.sli')
        if True and os.path.exists(pathSL):
            t0 = datetime.datetime.now()
            speclib = SpectralLibrary.readFrom(pathSL)

            dt = datetime.datetime.now() - t0
            print('Reading required : {}'.format(dt))
        else:
            speclib = createLargeSpeclib(2)

        t0 = datetime.datetime.now()
        w = SpectralLibraryWidget()

        w.addSpeclib(speclib)
        dt = datetime.datetime.now() - t0
        print('Adding speclib required : {}'.format(dt))

        self.showGui(w)

    def test_SpectralLibraryPlotColorScheme(self):

        self.assertIsInstance(SpectralLibraryPlotColorScheme.default(), SpectralLibraryPlotColorScheme)
        self.assertIsInstance(SpectralLibraryPlotColorScheme.dark(), SpectralLibraryPlotColorScheme)
        self.assertIsInstance(SpectralLibraryPlotColorScheme.bright(), SpectralLibraryPlotColorScheme)
        self.assertIsInstance(SpectralLibraryPlotColorScheme.fromUserSettings(), SpectralLibraryPlotColorScheme)

        b = SpectralLibraryPlotColorScheme.bright()
        b.saveToUserSettings()
        self.assertEqual(b, SpectralLibraryPlotColorScheme.fromUserSettings())
        d = SpectralLibraryPlotColorScheme.default()
        d.saveToUserSettings()
        self.assertEqual(d, SpectralLibraryPlotColorScheme.fromUserSettings())

    def test_SpectralLibraryPlotColorSchemeWidget(self):

        w = SpectralLibraryPlotColorSchemeWidget()
        self.assertIsInstance(w, SpectralLibraryPlotColorSchemeWidget)
        self.showGui(w)

    def test_SpeclibWidgetCurrentProfilOverlayerXUnit(self):

        sw = SpectralLibraryWidget()
        self.assertIsInstance(sw, SpectralLibraryWidget)
        pw = sw.plotWidget()
        self.assertIsInstance(pw, SpectralLibraryPlotWidget)
        self.assertEqual(pw.xUnit(), BAND_INDEX)
        slib = createSpeclib()


        xunits = []
        for p in slib:
            self.assertIsInstance(p, SpectralProfile)
            u = p.xUnit()
            if u not in xunits:
                xunits.append(u)

        sw = SpectralLibraryWidget(speclib=slib)
        self.assertEqual(sw.speclib(), slib)
        sw.applyAllPlotUpdates()

        sw = SpectralLibraryWidget()
        sp = slib[0]
        sw.setCurrentProfiles([sp])
        sw.applyAllPlotUpdates()


    def test_SpectraLibraryPlotDataItem(self):

        sl = createSpeclib()
        profile = sl[0]
        sp = SpectralProfilePlotDataItem(profile)

        plotStyle = defaultCurvePlotStyle()
        plotStyle.apply(sp)

        ps2 = PlotStyle.fromPlotDataItem(sp)

        self.assertEqual(plotStyle, ps2)


    def test_SpectralLibraryPlotWidget(self):

        speclib = SpectralLibrary.readFrom(speclibpath)



        pw = SpectralLibraryPlotWidget()
        self.assertIsInstance(pw, SpectralLibraryPlotWidget)
        self.assertTrue(pw.xUnit(), BAND_INDEX)

        p = speclib[0]
        sl = SpectralLibrary()
        sl.startEditing()
        pw.setSpeclib(sl)

        sl.addProfiles([p])
        self.assertTrue(pw.xUnit(), p.xUnit())


        w = QWidget()
        w.setLayout(QVBoxLayout())
        pw = SpectralLibraryPlotWidget()

        btn = QPushButton('Add speclib')
        btn.clicked.connect(lambda : pw.setSpeclib(speclib))
        w.layout().addWidget(pw)
        w.layout().addWidget(btn)


        self.assertIsInstance(pw.plotItem, pg.PlotItem)
        self.assertIsInstance(pw.plotItem.getViewBox(), SpectralViewBox)
        self.assertIsInstance(pw.plotItem.getAxis('bottom'), SpectralXAxis)



        plotItem = pw.getPlotItem()
        self.assertIsInstance(plotItem, pg.PlotItem)
        self.assertTrue(len(plotItem.dataItems) == 0)
        pw.setSpeclib(speclib)
        pw.updateSpectralProfilePlotItems()
        n = len([sp for sp in plotItem.dataItems if isinstance(sp, SpectralProfilePlotDataItem)])
        self.assertTrue(n == len(speclib))

        pw.setXUnit('nm')
        self.showGui(w)



class TestIO(TestCase):

    def setUp(self):
        print('RUN TEST {}'.format(self.id()))
        for file in vsiSpeclibs():
            gdal.Unlink(file)
            s = ""
        for s in SpectralLibrary.__refs__:
            del s
        SpectralLibrary.__refs__ = []
        QgsProject.instance().removeMapLayers(QgsProject.instance().mapLayers().keys())

        self.progressDialog = QProgressDialog()

    def tearDown(self) -> None:
        self.progressDialog.close()

    @classmethod
    def setUpClass(cls):
        super(TestIO, cls).setUpClass(cls)
        os.makedirs(TEST_DIR, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        super(TestIO, cls).tearDownClass()
        if os.path.isdir(TEST_DIR):
            shutil.rmtree(TEST_DIR, ignore_errors=True)

    def createSpeclib(self)->SpectralLibrary:
        return createSpeclib()

    def test_VSI(self):

        slib1 = self.createSpeclib()
        path = slib1.source()

        slib2 = SpectralLibrary.readFrom(path, progressDialog=self.progressDialog)
        self.assertIsInstance(slib2, SpectralLibrary)
        self.assertEqual(slib1, slib2)
        s = ""


    def test_jsonIO(self):

        slib = self.createSpeclib()
        pathJSON = tempfile.mktemp(suffix='.json', prefix='tmpSpeclib')

        # no additional info, no JSON file
        slib.writeJSONProperties(pathJSON)
        self.assertFalse(os.path.isfile(pathJSON))

        # add categorical info
        slib.startEditing()
        slib.addAttribute(QgsField('class1', QVariant.String, 'varchar'))
        slib.addAttribute(QgsField('class2', QVariant.Int, 'int'))
        slib.commitChanges()
        slib.startEditing()

        from qps.classification.classificationscheme import ClassificationScheme, ClassInfo, EDITOR_WIDGET_REGISTRY_KEY, classSchemeToConfig, classSchemeFromConfig


        cs = ClassificationScheme()
        cs.insertClass(ClassInfo(name='unclassified'))
        cs.insertClass(ClassInfo(name='class a', color=QColor('red')))
        cs.insertClass(ClassInfo(name='class b', color=QColor('blue')))


        idx1 = slib.fields().lookupField('class1')
        idx2 = slib.fields().lookupField('class2')

        config = classSchemeToConfig(cs)
        setup1 = QgsEditorWidgetSetup(EDITOR_WIDGET_REGISTRY_KEY, config)
        setup2 = QgsEditorWidgetSetup(EDITOR_WIDGET_REGISTRY_KEY, config)
        slib.setEditorWidgetSetup(idx1, setup1)
        slib.setEditorWidgetSetup(idx2, setup2)

        slib.writeJSONProperties(pathJSON)
        self.assertTrue(os.path.isfile(pathJSON))
        with open(pathJSON, 'r') as file:
            jsonData = json.load(file)
            self.assertTrue('class1' in jsonData.keys())
            self.assertTrue('class2' in jsonData.keys())

        slib.setEditorWidgetSetup(idx1, QgsEditorWidgetSetup('', {}))
        slib.setEditorWidgetSetup(idx2, QgsEditorWidgetSetup('', {}))
        data = slib.readJSONProperties(pathJSON)
        s = ""



    def test_CSV2(self):
        from qpstestdata import speclib
        SLIB = SpectralLibrary.readFrom(speclib, progressDialog=self.progressDialog)
        pathCSV = tempfile.mktemp(suffix='.csv', prefix='tmpSpeclib')
        #print(pathCSV)
        CSVSpectralLibraryIO.write(SLIB, pathCSV, progressDialog=self.progressDialog)

        self.assertTrue(os.path.isfile(pathCSV))
        dialect = CSVSpectralLibraryIO.canRead(pathCSV)
        self.assertTrue(dialect is not None)
        speclib2 = CSVSpectralLibraryIO.readFrom(pathCSV, dialect=dialect, progressDialog=self.progressDialog)
        self.assertTrue(len(SLIB) == len(speclib2))
        for i, (p1, p2) in enumerate(zip(SLIB[:], speclib2[:])):
            self.assertIsInstance(p1, SpectralProfile)
            self.assertIsInstance(p2, SpectralProfile)
            if p1 != p2:
                s = ""
            self.assertEqual(p1, p2)


        SLIB = self.createSpeclib()
        #pathCSV = os.path.join(os.path.dirname(__file__), 'speclibcvs2.out.csv')
        pathCSV = tempfile.mktemp(suffix='.csv', prefix='tmpSpeclib')
        print(pathCSV)
        CSVSpectralLibraryIO.write(SLIB, pathCSV, progressDialog=self.progressDialog)

        self.assertTrue(os.path.isfile(pathCSV))
        dialect = CSVSpectralLibraryIO.canRead(pathCSV)
        self.assertTrue(dialect is not None)
        speclib2 = CSVSpectralLibraryIO.readFrom(pathCSV, dialect=dialect, progressDialog=self.progressDialog)
        self.assertTrue(len(SLIB) == len(speclib2))
        for i, (p1, p2) in enumerate(zip(SLIB[:], speclib2[:])):
            self.assertIsInstance(p1, SpectralProfile)
            self.assertIsInstance(p2, SpectralProfile)
            self.assertEqual(p1.xValues(), p2.xValues())
            self.assertEqual(p1.yValues(), p2.yValues())
            if p1 != p2:
                s = ""
            self.assertEqual(p1, p2)


        #self.assertEqual(SLIB, speclib2)


        # addresses issue #8
        from qpstestdata import speclib
        SL1 = SpectralLibrary.readFrom(speclib, progressDialog=self.progressDialog)
        self.assertIsInstance(SL1, SpectralLibrary)

        pathCSV = tempfile.mktemp(suffix='.csv', prefix='tmpSpeclib')
        print(pathCSV)
        for dialect in [pycsv.excel_tab, pycsv.excel]:
            pathCSV = tempfile.mktemp(suffix='.csv', prefix='tmpSpeclib')
            CSVSpectralLibraryIO.write(SL1, pathCSV, dialect=dialect, progressDialog=self.progressDialog)
            d = CSVSpectralLibraryIO.canRead(pathCSV)
            self.assertEqual(d, dialect)
            SL2 = CSVSpectralLibraryIO.readFrom(pathCSV, dialect=dialect, progressDialog=self.progressDialog)
            self.assertIsInstance(SL2, SpectralLibrary)
            self.assertTrue(len(SL1) == len(SL2))

            for p1, p2 in zip(SL1[:], SL2[:]):
                self.assertIsInstance(p1, SpectralProfile)
                self.assertIsInstance(p2, SpectralProfile)
                if p1 != p2:
                    s = ""
                self.assertEqual(p1, p2)


        # addresses issue #8 loading modified CSV values

        SL = SpectralLibrary.readFrom(speclib, progressDialog=self.progressDialog)

        pathCSV = tempfile.mktemp(suffix='.csv', prefix='tmpSpeclib')
        CSVSpectralLibraryIO.write(SL, pathCSV, progressDialog=self.progressDialog)

        with open(pathCSV, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # change band values of b1 and b3

        WKT = None
        delimiter = '\t'
        for i in range(len(lines)):
            line = lines[i]
            if line.strip() in ['']:
                continue
            if line.startswith('#'):
                continue

            if line.startswith('WKT'):
                WKT = line.split(delimiter)
                continue


            parts = line.split(delimiter)
            parts[WKT.index('b1')] = '42.0'
            parts[WKT.index('b100')] = '42'
            line = delimiter.join(parts)
            lines[i] = line

        with open(pathCSV, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        SL2 = CSVSpectralLibraryIO.readFrom(pathCSV, progressDialog=self.progressDialog)

        self.assertEqual(len(SL), len(SL2))

        for p in SL2:
            self.assertIsInstance(p, SpectralProfile)
            self.assertEqual(p.yValues()[0], 42)
            self.assertEqual(p.yValues()[99], 42)


    def test_vector2speclib(self):

        lyrRaster = QgsRasterLayer(enmap)
        h, w = lyrRaster.height(), lyrRaster.width()

        factor = [0, 0.5, 1.]
        pxPositions = []

        for x in factor:
            for y in factor:
                pxPositions.append(QPoint(int(x * (w-1)), int(y * (h-1))))

        speclib1 = SpectralLibrary.readFromRasterPositions(enmap, pxPositions)

        ds = gdal.Open(enmap)
        data = ds.ReadAsArray()
        for i, px in enumerate(pxPositions):

            vector = data[:, px.y(), px.x()]

            profile = speclib1[i]

            self.assertIsInstance(profile, SpectralProfile)
            vector2 = profile.yValues()
            self.assertListEqual(list(vector), vector2)

        progress = QProgressDialog()

        speclib2 = SpectralLibrary.readFromVector(speclib1, lyrRaster, progressDialog=progress)
        self.assertIsInstance(speclib2, SpectralLibrary)
        self.assertEqual(len(speclib1), len(speclib2))
        self.assertTrue(speclib1.crs().toWkt() == speclib2.crs().toWkt())

        profiles1 = sorted(speclib1[:], key=lambda f:f.name())
        profiles2 = sorted(speclib1[:], key=lambda f:f.name())

        for p1, p2 in zip(profiles1, profiles2):
            self.assertIsInstance(p1, SpectralProfile)
            self.assertIsInstance(p2, SpectralProfile)
            self.assertListEqual(p1.yValues(), p2.yValues())
            self.assertTrue(p1.geometry().equals(p2.geometry()))

        uri = "MultiPoint?crs=epsg:4326";
        pathMultiPointLayer = r'C:\Users\geo_beja\Repositories\QGIS_Plugins\enmap-box\enmapboxtestdata\landcover_berlin_point.shp'
        pathRasterLayer = r'C:\Users\geo_beja\Repositories\QGIS_Plugins\enmap-box\enmapboxtestdata\enmap_berlin.bsq'
        vlMultiPoint = None

        if os.path.isfile(pathMultiPointLayer) and os.path.isfile(pathRasterLayer):
            vlMultiPoint = QgsVectorLayer(pathMultiPointLayer)
            rlEnMAP = QgsRasterLayer(pathRasterLayer)
            speclib3 = SpectralLibrary.readFromVector(vlMultiPoint, rlEnMAP, progressDialog=progress)

            self.assertIsInstance(speclib3, SpectralLibrary)
            self.assertTrue(len(speclib3) > 0)

    def test_reloadProfiles(self):
        lyr = QgsRasterLayer(enmap)
        QgsProject.instance().addMapLayer(lyr)
        lyr.setName('ENMAP')
        self.assertIsInstance(lyr, QgsRasterLayer)
        locations = []
        for x in range(lyr.width()):
            for y in range(lyr.height()):
                locations.append(QPoint(x, y))

        speclibA = SpectralLibrary.readFromRasterPositions(lyr.source(), locations)

        speclibREF = SpectralLibrary.readFromRasterPositions(lyr.source(), locations)
        speclibREF.setName('REF SPECLIB')
        self.assertIsInstance(speclibA, SpectralLibrary)
        self.assertTrue(len(locations) == len(speclibA))

        self.assertTrue(speclibA.isEditable() == False)

        # clean values
        speclibA.startEditing()
        idx = speclibA.fields().indexOf(FIELD_VALUES)
        for p in speclibA:
            self.assertIsInstance(p, SpectralProfile)
            speclibA.changeAttributeValue(p.id(), idx, None)
        self.assertTrue(speclibA.commitChanges())

        for p in speclibA:
            self.assertIsInstance(p, SpectralProfile)
            self.assertEqual(p.yValues(), [])

        # re-read values
        speclibA.selectAll()
        speclibA.startEditing()
        speclibA.reloadSpectralValues(enmap)
        self.assertTrue(speclibA.commitChanges())
        for a, b in zip(speclibA[:], speclibREF[:]):
            self.assertIsInstance(a, SpectralProfile)
            self.assertIsInstance(b, SpectralProfile)
            self.assertListEqual(a.xValues(), b.xValues())
            self.assertListEqual(a.yValues(), b.yValues())

        slw = SpectralLibraryWidget(speclib=speclibA)

        # clean values
        speclibA.startEditing()
        idx = speclibA.fields().indexOf(FIELD_VALUES)
        for p in speclibA:
            self.assertIsInstance(p, SpectralProfile)
            speclibA.changeAttributeValue(p.id(), idx, None)
        self.assertTrue(speclibA.commitChanges())

        self.showGui(slw)


    def test_EcoSIS(self):


        from qps.speclib.ecosis import EcoSISSpectralLibraryIO

        # 1. read
        from qpstestdata import DIR_ECOSIS
        for path in file_search(DIR_ECOSIS, '*.csv'):
            print('Read {}...'.format(path))
            self.assertTrue(EcoSISSpectralLibraryIO.canRead(path), msg='Unable to read {}'.format(path))
            sl = EcoSISSpectralLibraryIO.readFrom(path, progressDialog=self.progressDialog)
            self.assertIsInstance(sl, SpectralLibrary)
            self.assertTrue(len(sl) > 0)

        # 2. write
        speclib = self.createSpeclib()
        pathCSV = os.path.join(TEST_DIR, 'speclib.ecosys.csv')
        csvFiles = EcoSISSpectralLibraryIO.write(speclib, pathCSV, progressDialog=self.progressDialog)

        n = 0
        for p in csvFiles:
            self.assertTrue(os.path.isfile(p))
            self.assertTrue(EcoSISSpectralLibraryIO.canRead(p))

            slPart = EcoSISSpectralLibraryIO.readFrom(p, progressDialog=self.progressDialog)
            self.assertIsInstance(slPart, SpectralLibrary)


            n += len(slPart)

        self.assertEqual(len(speclib) - 1, n)




    def test_SPECCHIO(self):


        from qps.speclib.specchio import SPECCHIOSpectralLibraryIO

        # 1. read
        from qpstestdata import DIR_SPECCHIO
        for path in reversed(list(file_search(DIR_SPECCHIO, '*.csv'))):

            self.assertTrue(SPECCHIOSpectralLibraryIO.canRead(path))
            sl = SPECCHIOSpectralLibraryIO.readFrom(path, progressDialog=self.progressDialog)
            self.assertIsInstance(sl, SpectralLibrary)
            self.assertTrue(len(sl) > 0)

        # 2. write
        speclib = self.createSpeclib()
        pathCSV = os.path.join(TEST_DIR, 'speclib.specchio.csv')
        csvFiles = SPECCHIOSpectralLibraryIO.write(speclib, pathCSV, progressDialog=self.progressDialog)

        n = 0
        for p in csvFiles:
            self.assertTrue(os.path.isfile(p))
            self.assertTrue(SPECCHIOSpectralLibraryIO.canRead(p))

            slPart = SPECCHIOSpectralLibraryIO.readFrom(p, progressDialog=self.progressDialog)
            self.assertIsInstance(slPart, SpectralLibrary)


            n += len(slPart)

        self.assertEqual(len(speclib) - 1, n)


    def test_ASD(self):

        # read binary files
        from qps.speclib.asd import ASDSpectralLibraryIO, ASDBinaryFile
        from qpstestdata import DIR_ASD_BIN, DIR_ASD_TXT

        binaryFiles = list(file_search(DIR_ASD_BIN, '*.asd'))
        for path in binaryFiles:
            self.assertTrue(ASDSpectralLibraryIO.canRead(path))
            asdFile = ASDBinaryFile().readFromBinaryFile(path)

            self.assertIsInstance(asdFile, ASDBinaryFile)

            sl = ASDSpectralLibraryIO.readFrom(path, progressDialog=self.progressDialog)
            self.assertIsInstance(sl, SpectralLibrary)
            self.assertEqual(len(sl), 1)

        sl = ASDSpectralLibraryIO.readFrom(binaryFiles, progressDialog=self.progressDialog)
        self.assertIsInstance(sl, SpectralLibrary)
        self.assertEqual(len(sl), len(binaryFiles))

        textFiles = list(file_search(DIR_ASD_TXT, '*.asd.txt'))
        for path in textFiles:
            self.assertTrue(ASDSpectralLibraryIO.canRead(path))

            sl = ASDSpectralLibraryIO.readFrom(path, progressDialog=self.progressDialog)
            self.assertIsInstance(sl, SpectralLibrary)
            self.assertEqual(len(sl), 1)

        sl = ASDSpectralLibraryIO.readFrom(textFiles, progressDialog=self.progressDialog)
        self.assertIsInstance(sl, SpectralLibrary)
        self.assertEqual(len(sl), len(textFiles))

    def test_vectorlayer(self):

        slib = self.createSpeclib()


        from qps.speclib.vectorsources import VectorSourceSpectralLibraryIO

        extensions = ['.csv', '.gpkg', '.shp', '.kml', '.gpx']
        for ext in extensions:
            print('Test vector file type {}'.format(ext))
            path = tempfile.mktemp(suffix=ext, prefix='tmpSpeclib')

            # write
            writtenFiles = VectorSourceSpectralLibraryIO.write(slib, path, progressDialog=self.progressDialog)
            self.assertTrue(len(writtenFiles) > 0)

            # read
            results = []
            n = 0
            for file in writtenFiles:
                self.assertTrue(VectorSourceSpectralLibraryIO.canRead(file), msg='Failed to read speclib from {}'.format(file))
                sl = VectorSourceSpectralLibraryIO.readFrom(file, progressDialog=self.progressDialog)
                n += len(sl)
                self.assertIsInstance(sl, SpectralLibrary)
                results.append(sl)

            self.assertEqual(n, len(slib))



    def test_AbstractSpectralLibraryIOs(self):
        """
        A generic test to check all AbstractSpectralLibraryIO implementations
        """
        slib = createSpeclib()

        nFeatures = len(slib)
        nProfiles = 0
        for p in slib:
            if len(p.yValues()) > 0:
                nProfiles += 1

        for c in allSubclasses(AbstractSpectralLibraryIO):
            print('Test {}'.format(c.__name__))
            path = tempfile.mktemp(suffix='.csv', prefix='tmpSpeclib')
            writtenFiles = c.write(slib, path, progressDialog=self.progressDialog)

            # if it can write, it should read the profiles too
            if len(writtenFiles) > 0:

                n = 0
                for path in writtenFiles:
                    self.assertTrue(os.path.isfile(path), msg='Failed to write file. {}'.format(c))
                    sl = c.readFrom(path, progressDialog=self.progressDialog)
                    self.assertIsInstance(sl, SpectralLibrary)
                    n += len(sl)

                self.assertTrue(n == nProfiles or n == nFeatures)
            pass


    def test_ARTMO(self):

        from qpstestdata import DIR_ARTMO

        p = os.path.join(DIR_ARTMO, 'directional_reflectance.txt')

        from qps.speclib.artmo import ARTMOSpectralLibraryIO

        self.assertTrue(ARTMOSpectralLibraryIO.canRead(p))

        sl = ARTMOSpectralLibraryIO.readFrom(p, progressDialog=self.progressDialog)

        self.assertIsInstance(sl, SpectralLibrary)
        self.assertEqual(len(sl), 10)

    def test_CSV(self):
        # TEST CSV writing
        speclib = self.createSpeclib()

        # txt = CSVSpectralLibraryIO.asString(speclib)
        pathCSV = tempfile.mktemp(suffix='.csv', prefix='tmpSpeclib')
        pathCSV = os.path.join(os.path.dirname(__file__), 'speclibcvs3.out.csv')
        writtenFiles = speclib.exportProfiles(pathCSV)
        self.assertIsInstance(writtenFiles, list)
        self.assertTrue(len(writtenFiles) == 1)

        path = writtenFiles[0]
        lines = None
        with open(path, 'r') as f:
            lines = f.read()
        self.assertTrue(CSVSpectralLibraryIO.canRead(path), msg='Unable to read {}'.format(path))
        sl_read1 = CSVSpectralLibraryIO.readFrom(path, progressDialog=self.progressDialog)
        sl_read2 = SpectralLibrary.readFrom(path, progressDialog=self.progressDialog)

        self.assertTrue(len(sl_read1) > 0)
        self.assertIsInstance(sl_read1, SpectralLibrary)
        self.assertIsInstance(sl_read2, SpectralLibrary)

        self.assertEqual(len(sl_read1), len(speclib), msg='Should return {} instead of {} SpectralProfiles'.format(len(speclib), len(sl_read1)))

        profilesA = sorted(speclib.profiles(), key=lambda p: p.id())
        profilesB = sorted(sl_read1.profiles(), key=lambda p: p.attribute('fid'))

        for p1, p2 in zip(profilesA, profilesB):
            self.assertIsInstance(p1, SpectralProfile)
            self.assertIsInstance(p2, SpectralProfile)
            self.assertEqual(p1.name(), p2.name())
            self.assertEqual(p1.xUnit(), p2.xUnit())
            self.assertEqual(p1.yUnit(), p2.yUnit())

        self.SPECLIB = speclib

        try:
            os.remove(pathCSV)
        except:
            pass

    def test_findEnviHeader(self):

        binarypath = speclibpath

        hdr, bin = findENVIHeader(speclibpath)

        self.assertTrue(os.path.isfile(hdr))
        self.assertTrue(os.path.isfile(bin))

        self.assertTrue(bin == speclibpath)
        self.assertTrue(hdr.endswith('.hdr'))

        headerPath = hdr

        # is is possible to use the *.hdr
        hdr, bin = findENVIHeader(headerPath)

        self.assertTrue(os.path.isfile(hdr))
        self.assertTrue(os.path.isfile(bin))

        self.assertTrue(bin == speclibpath)
        self.assertTrue(hdr.endswith('.hdr'))


        sl1 = SpectralLibrary.readFrom(binarypath, progressDialog=self.progressDialog)
        sl2 = SpectralLibrary.readFrom(headerPath, progressDialog=self.progressDialog)

        self.assertEqual(sl1, sl2)


        # this should fail

        pathWrong = enmap
        hdr, bin = findENVIHeader(pathWrong)
        self.assertTrue((hdr, bin) == (None, None))


    def test_ENVI(self):


        pathESL = speclibpath


        csv = readCSVMetadata(pathESL)

        sl1 = EnviSpectralLibraryIO.readFrom(pathESL, progressDialog=self.progressDialog)

        self.assertIsInstance(sl1, SpectralLibrary)
        p0 = sl1[0]
        self.assertIsInstance(p0, SpectralProfile)

        self.assertEqual(sl1.fieldNames(), ['fid', 'name', 'source', 'values'])
        self.assertEqual(p0.fieldNames(), ['fid', 'name', 'source', 'values'])

        self.assertEqual(p0.attribute('name'), p0.name())


        sl2 = SpectralLibrary.readFrom(pathESL, progressDialog=self.progressDialog)
        self.assertIsInstance(sl2, SpectralLibrary)
        self.assertEqual(sl1, sl2)
        p1 = sl2[0]
        self.assertIsInstance(p1, SpectralProfile)
        self.assertIsInstance(p1.xValues(), list)


        # test ENVI Spectral Library
        pathTmp = tempfile.mktemp(prefix='tmpESL', suffix='.sli')
        writtenFiles = EnviSpectralLibraryIO.write(sl1, pathTmp, progressDialog=self.progressDialog)


        nWritten = 0
        for pathHdr in writtenFiles:
            self.assertTrue(os.path.isfile(pathHdr))
            self.assertTrue(pathHdr.endswith('.sli'))

            basepath = os.path.splitext(pathHdr)[0]
            pathHDR = basepath + '.hdr'
            pathCSV = basepath + '.csv'
            self.assertTrue(os.path.isfile(pathHDR))
            self.assertTrue(os.path.isfile(pathCSV))

            self.assertTrue(EnviSpectralLibraryIO.canRead(pathHdr))
            sl_read1 = EnviSpectralLibraryIO.readFrom(pathHdr, progressDialog=self.progressDialog)
            self.assertIsInstance(sl_read1, SpectralLibrary)

            for fieldA in sl1.fields():
                self.assertIsInstance(fieldA, QgsField)
                a = sl_read1.fields().lookupField(fieldA.name())
                self.assertTrue(a >= 0)
                fieldB = sl_read1.fields().at(a)
                self.assertIsInstance(fieldB, QgsField)
                #if fieldA.type() != fieldB.type():
                #    s  = ""
                #self.assertEqual(fieldA.type(), fieldB.type())




            sl_read2 = SpectralLibrary.readFrom(pathHdr, progressDialog=self.progressDialog)
            self.assertIsInstance(sl_read2, SpectralLibrary)

            print(sl_read1)

            self.assertTrue(len(sl_read1) > 0)
            self.assertEqual(sl_read1, sl_read2)
            nWritten += len(sl_read1)

        self.assertEqual(len(sl1), nWritten, msg='Written and restored {} instead {}'.format(nWritten, len(sl1)))

        # addresses issue #11:
        # No error is generated when trying (by accident) to read the ENVI header file instead of the .sli/.esl file itself.


        pathHdr = os.path.splitext(speclibpath)[0]+'.hdr'
        self.assertTrue(os.path.isfile(pathHdr))
        sl1 = SpectralLibrary.readFrom(speclibpath, progressDialog=self.progressDialog)
        sl2 = SpectralLibrary.readFrom(pathHdr, progressDialog=self.progressDialog)
        self.assertIsInstance(sl1, SpectralLibrary)
        self.assertTrue(len(sl1) > 0)
        #self.assertEqual(sl1, sl2)
        for p1, p2 in zip(sl1[:], sl2[:]):
            self.assertIsInstance(p1, SpectralProfile)
            self.assertIsInstance(p2, SpectralProfile)
            self.assertEqual(p1, p2)


class TestCore(TestCase):

    def setUp(self):
        print('RUN TEST {}'.format(self.id()))
        for file in vsiSpeclibs():
            gdal.Unlink(file)
            s = ""
        for s in SpectralLibrary.__refs__:
            del s
        SpectralLibrary.__refs__ = []
        qps.registerEditorWidgets()
        QgsProject.instance().removeMapLayers(QgsProject.instance().mapLayers().keys())

        self.progressDialog = None
        if True:
            self.progressDialog = QProgressDialog()
            self.progressDialog.setWindowTitle('TESTS')
            self.progressDialog.setVisible(False)

        self.SP = None
        self.SPECLIB = None

        self.lyr1 = QgsRasterLayer(hymap)
        self.lyr2 = QgsRasterLayer(enmap)
        self.layers = [self.lyr1, self.lyr2]
        QgsProject.instance().addMapLayers(self.layers)

    def tearDown(self):
        if isinstance(self.progressDialog, QProgressDialog):
            self.progressDialog.setVisible(False)
            self.progressDialog.close()
            self.progressDialog = None

        self.SP = None
        self.SPECLIB = None
        self.lyr1 = None
        self.lyr2 = None


    def createSpeclib(self):
        return createSpeclib()

    def test_fields(self):

        f1 = createQgsField('foo', 9999)

        self.assertEqual(f1.name(), 'foo')
        self.assertEqual(f1.type(), QVariant.Int)
        self.assertEqual(f1.typeName(), 'int')

        f2 = createQgsField('bar', 9999.)
        self.assertEqual(f2.type(), QVariant.Double)
        self.assertEqual(f2.typeName(), 'double')

        f3 = createQgsField('text', 'Hello World')
        self.assertEqual(f3.type(), QVariant.String)
        self.assertEqual(f3.typeName(), 'varchar')

        fields = QgsFields()
        fields.append(f1)
        fields.append(f2)
        fields.append(f3)

        serialized = qgsFields2str(fields)
        self.assertIsInstance(serialized,str)

        fields2 = str2QgsFields(serialized)
        self.assertIsInstance(fields2, QgsFields)
        self.assertEqual(fields.count(), fields2.count())
        for i in range(fields.count()):
            f1 = fields.at(i)
            f2 = fields2.at(i)
            self.assertEqual(f1.type(), f2.type())
            self.assertEqual(f1.name(), f2.name())
            self.assertEqual(f1.typeName(), f2.typeName())


    def test_AttributeDialog(self):

        SLIB = createSpeclib()

        d = AddAttributeDialog(SLIB)

        self.showGui(d)



    def test_SpectralProfile_BandBandList(self):

        sp = SpectralProfile()
        xvals = [1, 2, 3, 4, 5]
        yvals = [2, 3, 4, 5, 6]
        sp.setValues(x=xvals, y=yvals)
        self.assertEqual(len(xvals), sp.nb())
        self.assertIsInstance(sp.bbl(), list)
        self.assertListEqual(sp.bbl(), np.ones(len(xvals)).tolist())

        bbl = [1, 0, 1, 1, 1]
        sp.setValues(bbl=bbl)
        self.assertIsInstance(sp.bbl(), list)
        self.assertListEqual(sp.bbl(), bbl)

    def test_Serialization(self):


        import qps.speclib.spectrallibraries
        x = [1, 2, 3, 4, 5]
        y = [2, 3, 4, 5, 6]
        bbl = [1, 0, 1, 1, 0]
        xUnit = 'nm'
        yUnit = None

        reminder = qps.speclib.spectrallibraries.SERIALIZATION

        for mode in [SerializationMode.JSON, SerializationMode.PICKLE]:
            qps.speclib.spectrallibraries.SERIALIZATION = mode

            sl = SpectralLibrary()
            self.assertTrue(sl.startEditing())
            sp = SpectralProfile()
            sp.setValues(x=x, y=y, bbl=bbl, xUnit=xUnit, yUnit=yUnit)

            vd1 = sp.values()
            dump = encodeProfileValueDict(vd1)

            if mode == SerializationMode.JSON:
                self.assertIsInstance(dump, str)
            elif mode == SerializationMode.PICKLE:
                self.assertIsInstance(dump, QByteArray)

            vd2 = decodeProfileValueDict(dump)
            self.assertIsInstance(vd2, dict)
            self.assertEqual(vd1, vd2)
            sl.addProfiles([sp])
            self.assertTrue(sl.commitChanges())

            rawValues = sl.getFeature(sl.allFeatureIds()[0]).attribute(FIELD_VALUES)

            if mode == SerializationMode.JSON:
                self.assertIsInstance(rawValues, str)
            elif mode == SerializationMode.PICKLE:
                self.assertIsInstance(rawValues, QByteArray)



        qps.speclib.spectrallibraries.SERIALIZATION = reminder


    def test_SpectralProfile(self):

        # empty profile
        sp = SpectralProfile()
        d = sp.values()
        self.assertIsInstance(d, dict)
        for k in ['x', 'y', 'xUnit', 'yUnit']:
            self.assertTrue(k in d.keys())
            v = d[k]
            self.assertTrue(v == EMPTY_PROFILE_VALUES[k])
        self.assertEqual(sp.xValues(), [])
        self.assertEqual(sp.yValues(), [])


        y = [0.23, 0.4, 0.3, 0.8, 0.7]
        x = [300, 400, 600, 1200, 2500]
        with self.assertRaises(Exception):
            # we need y values
            sp.setValues(x=x)

        d = sp.values()
        self.assertIsInstance(d, dict)
        for k in ['x','y', 'yUnit', 'xUnit', 'bbl']:
            self.assertEqual(d[k], EMPTY_PROFILE_VALUES[k])


        sp.setValues(y=y)
        self.assertListEqual(sp.xValues(), list(range(len(y))))

        sp.setValues(x=x)
        self.assertListEqual(sp.xValues(), x)
        d = sp.values()
        self.assertListEqual(d['y'], y)
        self.assertListEqual(d['x'], x)



        sClone = sp.clone()
        self.assertIsInstance(sClone, SpectralProfile)
        self.assertEqual(sClone, sp)
        sClone.setId(-9999)
        self.assertEqual(sClone, sp)



        canvas = QgsMapCanvas()
        canvas.setLayers(self.layers)
        canvas.setExtent(self.lyr2.extent())
        canvas.setDestinationCrs(self.lyr1.crs())
        pos = SpatialPoint(self.lyr2.crs(), *self.lyr2.extent().center())
        profiles = SpectralProfile.fromMapCanvas(canvas, pos)
        self.assertIsInstance(profiles, list)
        self.assertEqual(len(profiles), 2)
        for p in profiles:
            self.assertIsInstance(p, SpectralProfile)
            self.assertIsInstance(p.geometry(), QgsGeometry)
            self.assertTrue(p.hasGeometry())


        yVal = [0.23, 0.4, 0.3, 0.8, 0.7]
        xVal = [300,400, 600, 1200, 2500]
        sp1 = SpectralProfile()
        sp1.setValues(x=xVal, y=yVal)


        self.assertEqual(xVal, sp1.xValues())
        self.assertEqual(yVal, sp1.yValues())

        name = 'missingAttribute'
        sp1.setMetadata(name, 'myvalue')
        self.assertTrue(name not in sp1.fieldNames())
        sp1.setMetadata(name, 'myvalue', addMissingFields=True)
        self.assertTrue(name in sp1.fieldNames())
        self.assertEqual(sp1.metadata(name), 'myvalue')
        sp1.removeField(name)
        self.assertTrue(name not in sp1.fieldNames())

        sp1.setXUnit('nm')
        self.assertEqual(sp1.xUnit(), 'nm')

        self.assertEqual(sp1, sp1)


        for sp2 in[sp1.clone(), copy.copy(sp1), sp1.__copy__()]:
            self.assertIsInstance(sp2, SpectralProfile)
            self.assertEqual(sp1, sp2)


        dump = pickle.dumps(sp1)
        sp2 = pickle.loads(dump)
        self.assertIsInstance(sp2, SpectralProfile)
        self.assertEqual(sp1, sp2)
        self.assertEqual(sp1.values(), sp2.values())


        dump = pickle.dumps([sp1, sp2])
        loads = pickle.loads(dump)

        for i, p1 in enumerate([sp1, sp2]):
            p2 = loads[i]
            self.assertIsInstance(p1, SpectralProfile)
            self.assertIsInstance(p2, SpectralProfile)
            self.assertEqual(p1.values(), p2.values())
            self.assertEqual(p1.name(), p2.name())
            self.assertEqual(p1.id(), p2.id())


        sp2 = SpectralProfile()
        sp2.setValues(x=xVal, y=yVal, xUnit='um')
        self.assertNotEqual(sp1, sp2)
        sp2.setValues(xUnit='nm')
        self.assertEqual(sp1, sp2)
        sp2.setYUnit('reflectance')
        #self.assertNotEqual(sp1, sp2)




        values = [('key','value'),('key', 100),('Üä','ÜmlÄute')]
        for md in values:
            k, d = md
            sp1.setMetadata(k,d)
            v2 = sp1.metadata(k)
            self.assertEqual(v2, None)

        for md in values:
            k, d = md
            sp1.setMetadata(k, d, addMissingFields=True)
            v2 = sp1.metadata(k)
            self.assertEqual(d, v2)

        self.SP = sp1


        dump = pickle.dumps(sp1)

        unpickled = pickle.loads(dump)
        self.assertIsInstance(unpickled, SpectralProfile)
        self.assertEqual(sp1, unpickled)
        self.assertEqual(sp1.values(), unpickled.values())
        self.assertEqual(sp1.geometry().asWkt(), unpickled.geometry().asWkt())
        dump = pickle.dumps([sp1, sp2])
        unpickled = pickle.loads(dump)
        self.assertIsInstance(unpickled, list)
        r1, r2 = unpickled
        self.assertEqual(sp1.values(), r1.values())
        self.assertEqual(sp2.values(), r2.values())
        self.assertEqual(sp2.geometry().asWkt(), r2.geometry().asWkt())




    def test_SpectralProfileReading(self):

        lyr = TestObjects.createRasterLayer()
        self.assertIsInstance(lyr, QgsRasterLayer)

        center = SpatialPoint.fromMapLayerCenter(lyr)
        extent = SpatialExtent.fromLayer(lyr)
        x,y = extent.upperLeft()

        outOfImage = SpatialPoint(center.crs(), x - 10, y + 10)

        sp = SpectralProfile.fromRasterLayer(lyr, center)
        self.assertIsInstance(sp, SpectralProfile)
        self.assertIsInstance(sp.xValues(), list)
        self.assertIsInstance(sp.yValues(), list)
        self.assertEqual(len(sp.xValues()), lyr.bandCount())
        self.assertEqual(len(sp.yValues()), lyr.bandCount())

        sp = SpectralProfile.fromRasterLayer(lyr, outOfImage)
        self.assertTrue(sp == None)

    def test_speclib_mimedata(self):

        sp1 = SpectralProfile()
        sp1.setName('Name A')
        sp1.setValues(y=[0, 4, 3, 2, 1], x=[450, 500, 750, 1000, 1500])

        sp2 = SpectralProfile()
        sp2.setName('Name B')
        sp2.setValues(y=[3, 2, 1, 0, 1], x=[450, 500, 750, 1000, 1500])

        sl1 = SpectralLibrary()

        self.assertEqual(sl1.name(), 'SpectralLibrary')
        sl1.setName('MySpecLib')
        self.assertEqual(sl1.name(), 'MySpecLib')

        sl1.startEditing()
        sl1.addProfiles([sp1, sp2])
        sl1.commitChanges()


        # test link
        mimeData = sl1.mimeData(MIMEDATA_SPECLIB_LINK)

        slRetrieved = SpectralLibrary.readFromMimeData(mimeData)
        self.assertEqual(slRetrieved, sl1)

        writeOnly = []
        for format in [MIMEDATA_SPECLIB_LINK, MIMEDATA_SPECLIB, MIMEDATA_TEXT]:
            print('Test MimeData I/O "{}"'.format(format))
            mimeData = sl1.mimeData(format)
            self.assertIsInstance(mimeData, QMimeData)

            if format in writeOnly:
                continue

            slRetrieved = SpectralLibrary.readFromMimeData(mimeData)
            self.assertIsInstance(slRetrieved, SpectralLibrary, 'Re-Import from MIMEDATA failed for MIME type "{}"'.format(format))

            n = len(slRetrieved)
            self.assertEqual(n, len(sl1))
            for p, pr in zip(sl1.profiles(), slRetrieved.profiles()):
                self.assertIsInstance(p, SpectralProfile)
                self.assertIsInstance(pr, SpectralProfile)
                self.assertEqual(p.fieldNames(), pr.fieldNames())
                if p.yValues() != pr.yValues():
                    s = ""
                self.assertEqual(p.yValues(), pr.yValues())

                self.assertEqual(p.xValues(), pr.xValues())
                self.assertEqual(p.xUnit(), pr.xUnit())
                self.assertEqual(p.name(), pr.name())
                self.assertEqual(p, pr)


            self.assertEqual(sl1, slRetrieved)


    def test_groupBySpectralProperties(self):

        sl1 = self.createSpeclib()
        groups = sl1.groupBySpectralProperties(excludeEmptyProfiles=False)
        self.assertTrue(len(groups) > 0)
        for key, profiles in groups.items():
            self.assertTrue(len(key) == 3)
            xvalues, xunit, yunit = key
            self.assertTrue(xvalues is None or isinstance(xvalues, tuple) and len(xvalues) > 0)
            self.assertTrue(xunit is None or isinstance(xunit, str) and len(xunit) > 0)
            self.assertTrue(yunit is None or isinstance(yunit, str) and len(yunit) > 0)

            self.assertIsInstance(profiles, list)
            self.assertTrue(len(profiles) > 0)

            l = len(profiles[0].xValues())

            for p in profiles:
                self.assertEqual(l, len(p.xValues()))
            s = ""



    def test_SpectralLibrary(self):

        self.assertListEqual(vsiSpeclibs(), [])
        self.assertTrue(len(SpectralLibrary.instances()) == 0)
        sp1 = SpectralProfile()
        sp1.setName('Name 1')
        sp1.setValues(y=[1, 1, 1, 1, 1], x=[450, 500, 750, 1000, 1500])

        sp2 = SpectralProfile()
        sp2.setName('Name 2')
        sp2.setValues(y=[2, 2, 2, 2, 2], x=[450, 500, 750, 1000, 1500])

        SLIB = SpectralLibrary()
        self.assertEqual(len(vsiSpeclibs()), 1)
        self.assertEqual(len(SpectralLibrary.instances()), 1)
        self.assertEqual(len(SpectralLibrary.instances()), 1)

        sl2 = SpectralLibrary()
        self.assertEqual(len(SpectralLibrary.__refs__), 2)
        self.assertEqual(len(vsiSpeclibs()), 2)
        self.assertEqual(len(SpectralLibrary.instances()), 2)
        self.assertEqual(len(SpectralLibrary.instances()), 2)

        del sl2
        self.assertEqual(len(SpectralLibrary.instances()), 1)

        self.assertEqual(SLIB.name(), 'SpectralLibrary')
        SLIB.setName('MySpecLib')
        self.assertEqual(SLIB.name(), 'MySpecLib')

        SLIB.startEditing()
        SLIB.addProfiles([sp1, sp2])
        SLIB.rollBack()
        self.assertEqual(len(SLIB), 0)

        SLIB.startEditing()
        SLIB.addProfiles([sp1, sp2])
        SLIB.commitChanges()
        self.assertEqual(len(SLIB), 2)

        # test subsetting
        p = SLIB[0]
        self.assertIsInstance(p, SpectralProfile)
        self.assertIsInstance(p.values(), dict)

        if p.values() != sp1.values():
            s = ""

        self.assertEqual(p.values(), sp1.values(), msg='Unequal values:\n\t{}\n\t{}'.format(str(p.values()), str(sp1.values())))
        self.assertEqual(SLIB[0].values(), sp1.values())

        #self.assertNotEqual(speclib[0], sp1) #because sl1 has an FID


        subset = SLIB[0:1]
        self.assertIsInstance(subset, list)
        self.assertEqual(len(subset), 1)


        self.assertEqual(set(SLIB.allFeatureIds()), set([1,2]))
        slSubset = SLIB.speclibFromFeatureIDs(fids=2)
        self.assertEqual(set(SLIB.allFeatureIds()), set([1, 2]))
        self.assertIsInstance(slSubset, SpectralLibrary)

        refs = list(SpectralLibrary.instances())
        self.assertTrue(len(refs) == 2)

        self.assertEqual(len(slSubset), 1)
        self.assertEqual(slSubset[0].values(), SLIB[1].values())

        n = len(vsiSpeclibs())
        dump = pickle.dumps(SLIB)
        restoredSpeclib = pickle.loads(dump)
        self.assertIsInstance(restoredSpeclib, SpectralLibrary)
        self.assertEqual(len(vsiSpeclibs()), n+1)
        self.assertEqual(len(SLIB), len(restoredSpeclib))

        for i in range(len(SLIB)):
            p1 = SLIB[i]
            r1 = restoredSpeclib[i]

            if p1.values() != r1.values():
                s  =""

            self.assertEqual(p1.values(), r1.values(), msg='dumped and restored values are not the same')

        restoredSpeclib.startEditing()
        restoredSpeclib.addProfiles([sp2])
        self.assertTrue(restoredSpeclib.commitChanges())
        self.assertNotEqual(SLIB, restoredSpeclib)
        self.assertEqual(restoredSpeclib[-1].values(), sp2.values())


        #read from image

        if self.lyr1.isValid():
            center1 = self.lyr1.extent().center()
            center2 = SpatialPoint.fromSpatialExtent(SpatialExtent.fromLayer(self.lyr1))
        else:
            center1 = SpatialExtent.fromRasterSource(self.lyr1.source()).spatialCenter()
            center2 = SpatialExtent.fromRasterSource(self.lyr1.source()).spatialCenter()
            s  =""
        SLIB = SpectralLibrary.readFromRasterPositions(hymap, center1)
        slSubset = SpectralLibrary.readFromRasterPositions(hymap, center2)
        restoredSpeclib = SpectralLibrary.readFromRasterPositions(hymap, [center1, center2])

        for sl in [SLIB, slSubset]:
            self.assertIsInstance(sl, SpectralLibrary)
            self.assertTrue(len(sl) == 1)
            self.assertIsInstance(sl[0], SpectralProfile)
            self.assertTrue(sl[0].hasGeometry())

        self.assertTrue(len(restoredSpeclib) == 2)

        n1 = len(SLIB)
        n2 = len(slSubset)

        SLIB.startEditing()
        SLIB.addProfiles(slSubset[:])
        self.assertTrue(len(SLIB) == n1+n2)
        SLIB.addProfiles(slSubset[:])
        self.assertTrue(len(SLIB) == n1 + n2 + n2)
        self.assertTrue(SLIB.commitChanges())

    def test_others(self):

        self.assertEqual(23, toType(int, '23'))
        self.assertEqual([23, 42], toType(int, ['23','42']))
        self.assertEqual(23., toType(float, '23'))
        self.assertEqual([23., 42.], toType(float, ['23','42']))

        self.assertTrue(findTypeFromString('23') is int)
        self.assertTrue(findTypeFromString('23.3') is float)
        self.assertTrue(findTypeFromString('xyz23.3') is str)
        self.assertTrue(findTypeFromString('') is str)

        regex = CSVSpectralLibraryIO.REGEX_BANDVALUE_COLUMN

        #REGEX to identify band value column names

        for text in ['b1', 'b1_']:
            match = regex.match(text)
            self.assertEqual(match.group('band'), '1')
            self.assertEqual(match.group('xvalue'), None)
            self.assertEqual(match.group('xunit'), None)


        match = regex.match('b1 23.34 nm')
        self.assertEqual(match.group('band'), '1')
        self.assertEqual(match.group('xvalue'), '23.34')
        self.assertEqual(match.group('xunit'), 'nm')


    def test_mergeSpeclibs(self):
        sp1 = self.createSpeclib()

        sp2 = SpectralLibrary.readFrom(speclibpath, progressDialog=self.progressDialog)

        self.assertIsInstance(sp1, SpectralLibrary)
        self.assertIsInstance(sp2, SpectralLibrary)

        n = len(sp1)
        with self.assertRaises(Exception):
            sp1.addSpeclib(sp2)
        self.assertTrue(len(sp1), n)

        sp1.startEditing()
        sp1.addSpeclib(sp2)
        self.assertTrue(len(sp1), n+len(sp2))




    def test_SpectralProfileEditorWidget(self):

        SLIB = self.createSpeclib()

        w = SpectralProfileEditorWidget()
        p = SLIB[-1]
        w.setProfileValues(p)

        self.showGui(w)

    def test_SpectralProfileValueTableModel(self):

        speclib = self.createSpeclib()
        p3 = speclib[2]
        self.assertIsInstance(p3, SpectralProfile)

        xUnit = p3.xUnit()
        yUnit = p3.yUnit()


        m = SpectralProfileValueTableModel()
        self.assertIsInstance(m, SpectralProfileValueTableModel)
        self.assertTrue(m.rowCount() == 0)
        self.assertTrue(m.columnCount() == 2)
        self.assertEqual('Y [-]', m.headerData(0, orientation=Qt.Horizontal, role=Qt.DisplayRole))
        self.assertEqual('X [-]', m.headerData(1, orientation=Qt.Horizontal, role=Qt.DisplayRole))

        m.setProfileData(p3)
        self.assertTrue(m.rowCount() == len(p3.values()['x']))
        self.assertEqual('Y [Reflectance]'.format(yUnit), m.headerData(0, orientation=Qt.Horizontal, role=Qt.DisplayRole))
        self.assertEqual('X [{}]'.format(xUnit), m.headerData(1, orientation=Qt.Horizontal, role=Qt.DisplayRole))

        m.setColumnValueUnit(0, '')

    def test_SpectralProfileEditorWidgetFactory(self):

        # init some other requirements
        print('initialize EnMAP-Box editor widget factories')
        # register Editor widgets, if not done before

        reg = QgsGui.editorWidgetRegistry()
        if len(reg.factories()) == 0:
            reg.initEditors()

        registerSpectralProfileEditorWidget()
        self.assertTrue(EDITOR_WIDGET_REGISTRY_KEY in reg.factories().keys())
        factory = reg.factories()[EDITOR_WIDGET_REGISTRY_KEY]
        self.assertIsInstance(factory, SpectralProfileEditorWidgetFactory)
        vl = self.createSpeclib()
        am = vl.actions()
        self.assertIsInstance(am, QgsActionManager)

        c = QgsMapCanvas()
        w = QWidget()
        w.setLayout(QVBoxLayout())
        dv = QgsDualView()
        dv.init(vl, c)
        dv.setView(QgsDualView.AttributeTable)
        dv.setAttributeTableConfig(vl.attributeTableConfig())
        cb = QCheckBox()
        cb.setText('Show Editor')
        def onClicked(b:bool):
            if b:
                dv.setView(QgsDualView.AttributeEditor)
            else:
                dv.setView(QgsDualView.AttributeTable)
        cb.clicked.connect(onClicked)
        w.layout().addWidget(dv)
        w.layout().addWidget(cb)

        w.resize(QSize(300, 250))
        print(vl.fields().names())
        look = vl.fields().lookupField
        #self.assertTrue(factory.fieldScore(vl, look(FIELD_FID)) == 0) #specialized support style + str len > 350
        #self.assertTrue(factory.fieldScore(vl, look(FIELD_NAME)) == 5)
        #self.assertTrue(factory.fieldScore(vl, look(FIELD_VALUES)) == 20)

        parent = QWidget()
        configWidget = factory.configWidget(vl, look(FIELD_VALUES), None)
        self.assertIsInstance(configWidget, SpectralProfileEditorConfigWidget)

        self.assertIsInstance(factory.createSearchWidget(vl, 0, dv), QgsSearchWidgetWrapper)


        eww = factory.create(vl, 0, None, dv )
        self.assertIsInstance(eww, SpectralProfileEditorWidgetWrapper)
        self.assertIsInstance(eww.widget(), SpectralProfileEditorWidget)

        eww.valueChanged.connect(lambda v: print('value changed: {}'.format(v)))

        fields = vl.fields()
        vl.startEditing()
        value = eww.value()
        f = vl.getFeature(1)
        self.assertTrue(vl.updateFeature(f))

        self.showGui([w, configWidget])


    def test_largeLibs(self):

        r = r'T:/4bj/20140615_fulllib_clean.sli'
        if os.path.isfile(r):
            import time

            pps_min = 1000 #minium number of profiles per second

            t0 = time.time()
            sl = SpectralLibrary.readFrom(r, progressDialog=self.progressDialog)
            self.assertIsInstance(sl, SpectralLibrary)
            self.assertTrue(len(sl) > 1000)

            t1 = time.time()
            pps = float(len(sl)) / (t1-t0)

            print('read ESL {}'.format(pps))
            #self.assertTrue(pps > pps_min, msg='spectra import took tooo long. Need to have {} profiles per second at least. got {}'.format(pps_min, pps))


            slw = SpectralLibraryWidget()


            QgsApplication.processEvents()

            time0 = time.time()
            slw.addSpeclib(sl)
            QgsApplication.processEvents()
            time1 = time.time()

            pps = float(len(sl)) / (time1 - time0)
            print('visualize ESL {}'.format(pps))

            QgsApplication.processEvents()

            if not self.showGui([slw]):
                self.assertTrue(pps > 5*60,
                                msg='spectra visualization took tooo long. Need to have {} profiles per second at least. got {}'.format(
                                    pps_min, pps))


    def test_multiinstances(self):

        sl1 = SpectralLibrary(name='A')
        sl2 = SpectralLibrary(name='B')

        self.assertIsInstance(sl1, SpectralLibrary)
        self.assertIsInstance(sl2, SpectralLibrary)
        self.assertNotEqual(id(sl1), id(sl2))

    def test_qmainwindow(self):

        w1 = QWidget()
        w1.setWindowTitle('Parent')
        w1.setLayout(QVBoxLayout())

        w2 = QMainWindow()
        w2.setWindowTitle('CENTRAL MAIN APP')
        l = QLabel('CENTRAL')
        w2.setCentralWidget(l)

        w1.layout().addWidget(w2)


        self.showGui(w1)

    def test_SpectralLibrary_readFromVector(self):

        from qpstestdata import enmap_pixel, landcover, enmap

        rl = QgsRasterLayer(enmap)
        vl = QgsVectorLayer(enmap_pixel)

        progressDialog = QProgressDialog()
        #progressDialog.show()

        info ='Test read from \n'+ \
              'Vector: {}\n'.format(vl.crs().description()) + \
              'Raster: {}\n'.format(rl.crs().description())
        print(info)

        sl = SpectralLibrary.readFromVector(vl, rl, progressDialog=progressDialog)
        self.assertIsInstance(sl, SpectralLibrary)
        self.assertTrue(len(sl) > 0, msg='Failed to read SpectralProfiles')
        self.assertEqual(len(sl), rl.width() * rl.height())

        self.assertTrue(progressDialog.value(), [-1, progressDialog.maximum()])

        data = gdal.Open(enmap).ReadAsArray()
        nb, nl, ns = data.shape

        for p in sl:
            self.assertIsInstance(p, SpectralProfile)

            x = p.attribute('px_x')
            y = p.attribute('px_y')
            yValues = p.values()['y']
            yValues2 = list(data[:, y, x])
            self.assertListEqual(yValues, yValues2)
            s = ""

        self.assertTrue(sl.crs() != vl.crs())


        info ='Test read from \n'+ \
              'Vector: {} (speclib)\n'.format(sl.crs().description()) + \
              'Raster: {}\n'.format(rl.crs().description())
        print(info)


        sl2 = SpectralLibrary.readFromVector(sl, rl)
        self.assertIsInstance(sl, SpectralLibrary)
        self.assertTrue(len(sl2) > 0, msg='Failed to re-read SpectralProfiles')
        self.assertEqual(sl, sl2)

        rl = QgsRasterLayer(enmap)
        vl = QgsVectorLayer(landcover)
        sl = SpectralLibrary.readFromVector(vl, rl)
        self.assertIsInstance(sl, SpectralLibrary)
        self.assertTrue(len(sl) > 0)


    def test_mergeSpeclibSpeed(self):

        from qpstestdata import speclib


        sl1 = SpectralLibrary.readFrom(speclib, progressDialog=self.progressDialog)

        sl2 = SpectralLibrary()

        n = 3000
        p = sl1[0]
        profiles = []

        for i in range(n):
            profiles.append(p.clone())
        sl2.startEditing()
        sl2.addProfiles(profiles, addMissingFields=True)
        sl2.commitChanges()

        sl2.startEditing()
        sl2.addSpeclib(sl2)
        sl2.commitChanges()

        self.assertEqual(len(sl2), n*2)



        s = ""
    def test_speclibImportSpeed(self):

        pathRaster = r'C:\Users\geo_beja\Repositories\QGIS_Plugins\enmap-box\enmapboxtestdata\enmap_berlin.bsq'
        #pathPoly = r'C:\Users\geo_beja\Repositories\QGIS_Plugins\enmap-box\enmapboxtestdata\landcover_berlin_polygon.shp'
        pathPoly = r'C:\Users\geo_beja\Repositories\QGIS_Plugins\enmap-box\enmapboxtestdata\landcover_berlin_point.shp'

        for p in [pathRaster, pathPoly]:
            if not os.path.isfile(p):
                return

        progressDialog = QProgressDialog()
        #progressDialog.show()
        vl = QgsVectorLayer(pathPoly)
        vl.setName('Polygons')
        rl = QgsRasterLayer(pathRaster)
        rl.setName('Raster Data')
        if not vl.isValid() and rl.isValid():
            return

        max_spp = 1 # seconds per profile

        def timestats(t0, sl, info='time'):
            dt = time.time() - t0
            spp = dt / len(sl)
            pps = len(sl) / dt
            print('{}: dt={}sec spp={} pps={}'.format(info, dt, spp, pps ))
            return dt, spp, pps

        t0 = time.time()
        sl = SpectralLibrary.readFromVector(vl, rl, progressDialog=progressDialog)
        dt, spp, pps = timestats(t0, sl, info='read profiles')
        self.assertTrue(spp <= max_spp, msg='{} seconds per profile are too much!')

        self.assertTrue(progressDialog.value() == -1)
        t0 = time.time()
        sl.startEditing()
        sl.addSpeclib(sl)
        sl.commitChanges()
        dt, spp, pps = timestats(t0, sl, info='merge speclibs')
        self.assertTrue(spp <= max_spp, msg='too slow!')


        sl0 = SpectralLibrary()
        t0 = time.time()
        sl0.startEditing()
        sl0.addSpeclib(sl)
        dt, spp, pps = timestats(t0, sl, info='merge speclibs2')
        self.assertTrue(spp <= max_spp, msg='too slow!')


        w = SpectralLibraryWidget()

        t0 = time.time()
        w.addSpeclib(sl)

        dt = time.time()-t0

        QgsProject.instance().addMapLayers([vl, rl])
        w = SpectralLibraryWidget()
        self.showGui(w)

    def test_SpectralProfileImportPointsDialog(self):

        lyrRaster = QgsRasterLayer(enmap)
        lyrRaster.setName('EnMAP')
        h, w = lyrRaster.height(), lyrRaster.width()

        pxPositions = [QPoint(0, 0), QPoint(w - 1, h - 1)]

        speclib1 = SpectralLibrary.readFromRasterPositions(enmap, pxPositions)
        speclib1.setName('Extracted Spectra')
        self.assertIsInstance(speclib1, SpectralLibrary)
        self.assertTrue(len(speclib1) > 0)

        vl1 = TestObjects.createVectorLayer(QgsWkbTypes.Polygon)
        vl2 = TestObjects.createVectorLayer(QgsWkbTypes.LineGeometry)
        vl3 = TestObjects.createVectorLayer(QgsWkbTypes.Point)
        QgsProject.instance().addMapLayers([speclib1, lyrRaster, vl1, vl2, vl3])

        d = SpectralProfileImportPointsDialog()
        self.assertIsInstance(d, QDialog)
        d.setRasterSource(lyrRaster)
        d.setVectorSource(speclib1)

        self.assertEqual(lyrRaster, d.rasterSource())
        self.assertEqual(speclib1, d.vectorSource())

        slib = d.speclib()
        self.assertIsInstance(slib, SpectralLibrary)

        self.showGui(d)

    def test_SpectralLibraryPanel(self):

        sp = SpectralLibraryPanel()


        self.showGui(sp)


    def test_SpectralLibraryWidgetProgressDialog(self):

        slib = createLargeSpeclib(3000)
        sw = SpectralLibraryWidget()

        QApplication.processEvents()
        #sw.addSpeclib(slib)
        #QApplication.processEvents()

        self.showGui(sw)


    def test_SpectralLibraryWidget(self):

        from qpstestdata import enmap, landcover, enmap_pixel

        l1 = QgsRasterLayer(enmap, 'EnMAP')
        l2 = QgsVectorLayer(landcover, 'LandCover')
        l3 = QgsVectorLayer(enmap_pixel, 'Points of Interest')
        QgsProject.instance().addMapLayers([l1, l2, l3])


        speclib = SpectralLibrary.readFrom(speclibpath, progressDialog=self.progressDialog)
        slw = SpectralLibraryWidget(speclib=speclib)

        QgsProject.instance().addMapLayer(slw.speclib())

        self.assertEqual(slw.speclib(), speclib)
        self.assertIsInstance(slw.speclib(), SpectralLibrary)
        fieldNames = slw.speclib().fieldNames()
        self.assertIsInstance(fieldNames, list)

        for mode in list(SpectralLibraryWidget.CurrentProfilesMode):
            assert isinstance(mode, SpectralLibraryWidget.CurrentProfilesMode)
            slw.setCurrentProfilesMode(mode)
            assert slw.currentProfilesMode() == mode

        cs = [speclib[0], speclib[3], speclib[-1]]
        l = len(speclib)
        self.assertTrue(slw.speclib() == speclib)

        self.assertTrue(len(slw.currentSpectra()) == 0)
        slw.setCurrentProfilesMode(SpectralLibraryWidget.CurrentProfilesMode.block)
        slw.setCurrentSpectra(cs)
        self.assertTrue(len(slw.currentSpectra()) == 0)

        slw.setCurrentProfilesMode(SpectralLibraryWidget.CurrentProfilesMode.automatically)
        slw.setCurrentSpectra(cs)
        self.assertTrue(len(slw.currentSpectra()) == 0)

        slw.setCurrentProfilesMode(SpectralLibraryWidget.CurrentProfilesMode.normal)
        slw.setCurrentSpectra(cs)
        self.assertTrue(len(slw.currentSpectra()) == 3)

        speclib.selectByIds([1, 2, 3])

        n = len(speclib)
        sids = speclib.selectedFeatureIds()

        self.assertTrue(len(sids) > 0)
        slw.copySelectedFeatures()
        slw.cutSelectedFeatures()
        slw.pasteFeatures()

        self.assertEqual(n, len(speclib))


        if False:
            sl2 = self.createSpeclib()
            slw.addSpeclib(sl2)

        self.showGui(slw)


    def test_SpectralLibraryWidgetCanvas(self):

        # speclib = self.createSpeclib()

        lyr = QgsRasterLayer(hymap)
        h, w = lyr.height(), lyr.width()
        speclib = SpectralLibrary.readFromRasterPositions(enmap, [QPoint(0,0), QPoint(w-1, h-1), QPoint(2, 2)])
        slw = SpectralLibraryWidget(speclib=speclib)


        QgsProject.instance().addMapLayers([lyr, slw.speclib()])

        canvas = QgsMapCanvas()

        canvas.setLayers([lyr, slw.speclib()])
        canvas.setDestinationCrs(slw.speclib().crs())
        canvas.setExtent(slw.speclib().extent())


        def setLayers():
            canvas.mapSettings().setDestinationCrs(slw.mCanvas.mapSettings().destinationCrs())
            canvas.setExtent(slw.canvas().extent())
            canvas.setLayers(slw.canvas().layers())

        slw.sigMapCenterRequested.connect(setLayers)
        slw.sigMapExtentRequested.connect(setLayers)

        self.showGui([canvas, slw])

    def test_editing(self):

        slib = self.createSpeclib()
        self.assertTrue(len(slib) > 0)
        slw = SpectralLibraryWidget()
        slw.speclib().startEditing()
        slw.speclib().addSpeclib(slib)

        slw.actionToggleEditing.setChecked(True)

        #self.assertTrue()
        self.showGui(slw)


    def test_speclibAttributeWidgets(self):

        import qps
        qps.registerEditorWidgets()
        speclib = createSpeclib()

        slw = SpectralLibraryWidget(speclib=speclib)

        import qps.layerproperties
        properties = qps.layerproperties.VectorLayerProperties(speclib, None)

        self.showGui([slw, properties])




    def test_toolbarStackedActions(self):

        tb = QToolBar()
        a1 = tb.addAction('Action1')
        a2 = tb.addAction('ActionA2')

        a21 = QAction('A2.1')
        a22 = QAction('A2.2')
        a22.setCheckable(True)

        setToolButtonDefaultActionMenu(a2, [a21, a22])


        btn2 = tb.findChildren(QToolButton)[2]
        self.assertIsInstance(btn2, QToolButton)

        self.showGui(tb)

if __name__ == '__main__':

    unittest.main()

