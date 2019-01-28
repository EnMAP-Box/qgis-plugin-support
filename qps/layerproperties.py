# -*- coding: utf-8 -*-
# noinspection PyPep8Naming
"""
***************************************************************************
    layerproperties.py
    ---------------------
    Date                 : August 2017
    Copyright            : (C) 2017 by Benjamin Jakimow
    Email                : benjamin.jakimow@geo.hu-berlin.de
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 3 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""


import collections
import os
import re

from osgeo import gdal, ogr, osr
import numpy as np
from qgis.gui import *
from qgis.core import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtXml import QDomDocument

from qps.utils import *
from qps.models import OptionListModel, Option
from qps.classification.classificationscheme import ClassificationScheme, ClassInfo

"""
class RasterLayerProperties(QgsOptionsDialogBase):
    def __init__(self, lyr, canvas, parent, fl=Qt.Widget):
        super(RasterLayerProperties, self).__init__("RasterLayerProperties", parent, fl)
        # self.setupUi(self)
        self.initOptionsBase(False)
        title = "Layer Properties - {}".format(lyr.name())
        self.restoreOptionsBaseUi(title)
"""


"""
    RASTERRENDERER_CREATE_FUNCTIONS['multibandcolor'] = MultiBandColorRendererWidget.create
    RASTERRENDERER_CREATE_FUNCTIONS['multibandcolor (QGIS)'] = QgsMultiBandColorRendererWidget.create
    RASTERRENDERER_CREATE_FUNCTIONS['paletted'] = 
    RASTERRENDERER_CREATE_FUNCTIONS['singlebandgray'] = 
    RASTERRENDERER_CREATE_FUNCTIONS['singlebandgray (QGIS)'] = QgsSingleBandGrayRendererWidget.create
    RASTERRENDERER_CREATE_FUNCTIONS['singlebandpseudocolor'] = SingleBandPseudoColorRendererWidget.create
    RASTERRENDERER_CREATE_FUNCTIONS['singlebandpseudocolor (QGIS)'] = QgsSingleBandPseudoColorRendererWidget.create
"""

RENDER_CLASSES = {}
RENDER_CLASSES['rasterrenderer'] = {
    'singlebandpseudocolor':QgsSingleBandPseudoColorRenderer,
    'singlebandgray': QgsSingleBandGrayRenderer,
    'paletted':QgsPalettedRasterRenderer,
    'multibandcolor': QgsMultiBandColorRenderer,
    'hillshade': QgsHillshadeRenderer
}
RENDER_CLASSES['renderer-v2'] = {
    'categorizedSymbol':QgsCategorizedSymbolRenderer,
    'singleSymbol':QgsSingleSymbolRenderer
}
DUMMY_RASTERINTERFACE = QgsSingleBandGrayRenderer(None, 0)


MDF_QGIS_LAYER_STYLE = 'application/qgis.style'
MDF_TEXT_PLAIN = 'text/plain'

def rendererFromXml(xml):
    """
    Reads a string `text` and returns the first QgsRasterRenderer or QgsFeatureRenderer (if defined).
    :param xml: QMimeData | QDomDocument
    :return:
    """

    if isinstance(xml, QMimeData):
        for format in [MDF_QGIS_LAYER_STYLE, MDF_TEXT_PLAIN]:
        #for format in ['application/qgis.style', 'text/plain']:
            if format in xml.formats():
                dom  = QDomDocument()
                dom.setContent(xml.data(format))
                return rendererFromXml(dom)
        return None

    elif isinstance(xml, str):
        dom = QDomDocument()
        dom.setContent(xml)
        return rendererFromXml(dom)

    assert isinstance(xml, QDomDocument)
    root = xml.documentElement()
    for baseClass, renderClasses in RENDER_CLASSES.items():
        elements = root.elementsByTagName(baseClass)
        if elements.count() > 0:
            elem = elements.item(0).toElement()
            typeName = elem.attributes().namedItem('type').nodeValue()
            if typeName in renderClasses.keys():
                rClass = renderClasses[typeName]
                if baseClass == 'rasterrenderer':

                    return rClass.create(elem, DUMMY_RASTERINTERFACE)
                elif baseClass == 'renderer-v2':
                    context = QgsReadWriteContext()
                    return rClass.load(elem, context)
            else:
                print(typeName)
                s =""
    return None

def defaultRasterRenderer(layer:QgsRasterLayer, bandIndices:list=None)->QgsRasterRenderer:
    """
    Returns a default Raster Renderer.
    See https://bitbucket.org/hu-geomatics/enmap-box/issues/166/default-raster-visualization
    :param layer: QgsRasterLayer
    :return: QgsRasterRenderer
    """

    renderer = None
    defaultRenderer = layer.renderer()
    if not isinstance(layer, QgsRasterLayer):
        return None


    nb = layer.bandCount()


    if isinstance(bandIndices, list):
        bandIndices = [b for b in bandIndices if b >=0 and b < nb]
        l = len(bandIndices)
        if l == 0:
            bandIndices = None
        if l >= 3:
            bandIndices = bandIndices[0:3]
        elif l < 3:
            bandIndices = bandIndices[0:1]

    if not isinstance(bandIndices, list):
        if nb >= 3:
            if isinstance(defaultRenderer, QgsMultiBandColorRenderer):
                bandIndices = [defaultRenderer.redBand()-1, defaultRenderer.greenBand()-1, defaultRenderer.blueBand()-1]
            else:
                bandIndices = [2,1,0]
        else:
            bandIndices = [0]

    assert isinstance(bandIndices, list)

    bandStats = [layer.dataProvider().bandStatistics(b + 1, sampleSize=256) for b in bandIndices]
    dp = layer.dataProvider()
    assert isinstance(dp, QgsRasterDataProvider)

    #classification ? -> QgsPalettedRasterRenderer
    classes = ClassificationScheme.fromMapLayer(layer)

    if isinstance(classes, ClassificationScheme):
        r = classes.rasterRenderer(band=bandIndices[0])
        r.setInput(layer.dataProvider())
        return r

    #single-band / two bands -> QgsSingleBandGrayRenderer
    if len(bandStats) < 3:
        b = bandIndices[0]+1
        stats = bandStats[0]
        assert isinstance(stats, QgsRasterBandStats)
        dt = dp.dataType(b)
        ce = QgsContrastEnhancement(dt)

        assert isinstance(ce, QgsContrastEnhancement)
        ce.setContrastEnhancementAlgorithm(QgsContrastEnhancement.StretchToMinimumMaximum, True)

        if dt == Qgis.Byte:
            if stats.minimumValue == 0 and stats.maximumValue == 1:
                #handle mask, strecht them over larger range
                ce.setMinimumValue(stats.minimumValue)
                ce.setMaximumValue(stats.maximumValue)
            else:
                ce.setMinimumValue(0)
                ce.setMaximumValue(255)
        else:
            vmin, vmax = layer.dataProvider().cumulativeCut(b, 0.02, 0.98)
            ce.setMinimumValue(vmin)
            ce.setMaximumValue(vmax)

        r = QgsSingleBandGrayRenderer(layer.dataProvider(), b)
        r.setContrastEnhancement(ce)
        return r

    # 3 or more bands -> RGB
    if len(bandStats) >= 3:
        bands = [b+1 for b in bandIndices[0:3]]
        contrastEnhancements = [QgsContrastEnhancement(dp.dataType(b)) for b in bands]
        ceR, ceG, ceB = contrastEnhancements

        for i, b in enumerate(bands):
            dt = dp.dataType(b)
            ce = contrastEnhancements[i]

            assert isinstance(ce, QgsContrastEnhancement)
            ce.setContrastEnhancementAlgorithm(QgsContrastEnhancement.StretchToMinimumMaximum, True)
            vmin, vmax = layer.dataProvider().cumulativeCut(b, 0.02, 0.98)
            if dt == Qgis.Byte:
                #standard RGB photo?
                if False and layer.bandCount() == 3:
                    ce.setMinimumValue(0)
                    ce.setMaximumValue(255)
                else:
                    ce.setMinimumValue(vmin)
                    ce.setMaximumValue(vmax)
            else:
                ce.setMinimumValue(vmin)
                ce.setMaximumValue(vmax)
        R, G, B = bands
        r = QgsMultiBandColorRenderer(layer.dataProvider(), R,G,B, None, None, None)
        r.setRedContrastEnhancement(ceR)
        r.setGreenContrastEnhancement(ceG)
        r.setBlueContrastEnhancement(ceB)
        r.setRedBand(R)
        r.setGreenBand(G)
        r.setBlueBand(B)
        return r
    if nb >= 3:
        pass

    return defaultRenderer


def rendererToXml(layerOrRenderer, geomType:QgsWkbTypes=None):
    """
    Returns a renderer XML representation
    :param layerOrRenderer: QgsRasterRender | QgsFeatureRenderer
    :return: QDomDocument
    """
    doc = QDomDocument()
    err = ''
    if isinstance(layerOrRenderer, QgsRasterLayer):
        return rendererToXml(layerOrRenderer.renderer())
    elif isinstance(layerOrRenderer, QgsVectorLayer):
        geomType = layerOrRenderer.geometryType()
        return rendererToXml(layerOrRenderer.renderer(), geomType=geomType)
    elif isinstance(layerOrRenderer, QgsRasterRenderer):
        #create a dummy raster layer
        import uuid
        xml = """<VRTDataset rasterXSize="1" rasterYSize="1">
                  <GeoTransform>  0.0000000000000000e+00,  1.0000000000000000e+00,  0.0000000000000000e+00,  0.0000000000000000e+00,  0.0000000000000000e+00, -1.0000000000000000e+00</GeoTransform>
                  <VRTRasterBand dataType="Float32" band="1">
                    <Metadata>
                      <MDI key="STATISTICS_MAXIMUM">0</MDI>
                      <MDI key="STATISTICS_MEAN">0</MDI>
                      <MDI key="STATISTICS_MINIMUM">0</MDI>
                      <MDI key="STATISTICS_STDDEV">0</MDI>
                    </Metadata>
                    <Description>Band 1</Description>
                    <Histograms>
                      <HistItem>
                        <HistMin>0</HistMin>
                        <HistMax>0</HistMax>
                        <BucketCount>1</BucketCount>
                        <IncludeOutOfRange>0</IncludeOutOfRange>
                        <Approximate>0</Approximate>
                        <HistCounts>0</HistCounts>
                      </HistItem>
                    </Histograms>
                  </VRTRasterBand>
                </VRTDataset>
                """
        path = '/vsimem/{}.vrt'.format(uuid.uuid4())
        drv = gdal.GetDriverByName('VRT')
        assert isinstance(drv, gdal.Driver)
        write_vsimem(path, xml)
        ds = gdal.Open(path)
        assert isinstance(ds, gdal.Dataset)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        ds.SetProjection(srs.ExportToWkt())
        ds.FlushCache()
        lyr = QgsRasterLayer(path)
        assert lyr.isValid()
        lyr.setRenderer(layerOrRenderer.clone())
        err = lyr.exportNamedStyle(doc)
        #remove dummy raster layer
        lyr = None
        drv.Delete(path)

    elif isinstance(layerOrRenderer, QgsFeatureRenderer) and geomType is not None:
        #todo: distinguish vector type from requested renderer
        typeName = QgsWkbTypes.geometryDisplayString(geomType)
        lyr = QgsVectorLayer('{}?crs=epsg:4326&field=id:integer'.format(typeName), 'dummy', 'memory')
        lyr.setRenderer(layerOrRenderer.clone())
        err = lyr.exportNamedStyle(doc)
        lyr = None
    else:
        raise NotImplementedError()


    return doc

def pasteStyleToClipboard(layer: QgsMapLayer):

    xml = rendererToXml(layer)
    if isinstance(xml, QDomDocument):
        md = QMimeData()
        # ['application/qgis.style', 'text/plain']

        md.setData('application/qgis.style', xml.toByteArray())
        md.setData('text/plain', xml.toByteArray())
        QApplication.clipboard().setMimeData(md)

def pasteStyleFromClipboard(layer:QgsMapLayer):
    mimeData = QApplication.clipboard().mimeData()
    renderer = rendererFromXml(mimeData)
    if isinstance(renderer, QgsRasterRenderer) and isinstance(layer, QgsRasterLayer):
        layer.setRenderer(renderer)
        layer.triggerRepaint()

    elif isinstance(renderer, QgsFeatureRenderer) and isinstance(layer, QgsVectorLayer):
        layer.setRenderer(renderer)
        layer.triggerRepaint()


class RendererWidgetModifications(object):


    def __init__(self):
        self.mBandComboBoxes = []

    def modifyGridLayout(self):
        gridLayoutOld = self.layout().children()[0]
        self.gridLayout = QGridLayout()
        while gridLayoutOld.count() > 0:
            w = gridLayoutOld.takeAt(0)
            w = w.widget()
            gridLayoutOld.removeWidget(w)
            w.setVisible(False)
            setattr(self, w.objectName(), w)
        self.layout().removeItem(gridLayoutOld)
        self.layout().insertItem(0, self.gridLayout)
        self.gridLayout.setSpacing(2)
        self.layout().addStretch()

    def connectSliderWithBandComboBox(self, slider, combobox):
        """
        Connects a band-selection slider with a band-selection combobox
        :param widget: QgsRasterRendererWidget
        :param slider: QSlider to show the band number
        :param combobox: QComboBox to show the band name
        :return:
        """
        assert isinstance(self, QgsRasterRendererWidget)
        assert isinstance(slider, QSlider)
        assert isinstance(combobox, QComboBox)

        # init the slider
        nb = self.rasterLayer().dataProvider().bandCount()
        slider.setTickPosition(QSlider.TicksAbove)
        slider.valueChanged.connect(combobox.setCurrentIndex)
        slider.setMinimum(1)
        slider.setMaximum(nb)
        intervals = [1, 2, 5, 10, 25, 50]
        for interval in intervals:
            if nb / interval < 10:
                break
        slider.setTickInterval(interval)
        slider.setPageStep(interval)

        def onBandValueChanged(self, idx, slider):
            assert isinstance(self, QgsRasterRendererWidget)
            assert isinstance(idx, int)
            assert isinstance(slider, QSlider)

            # i = slider.value()
            slider.blockSignals(True)
            slider.setValue(idx)
            slider.blockSignals(False)

            # self.minMaxWidget().setBands(myBands)
            # self.widgetChanged.emit()

        if self.comboBoxWithNotSetItem(combobox):
            combobox.currentIndexChanged[int].connect(lambda idx: onBandValueChanged(self, idx, slider))
        else:
            combobox.currentIndexChanged[int].connect(lambda idx: onBandValueChanged(self, idx + 1, slider))

    def comboBoxWithNotSetItem(self, cb):
        assert isinstance(cb, QComboBox)
        return cb.itemData(0, role=Qt.DisplayRole).lower() == 'not set'

    def setLayoutItemVisibility(self, grid, isVisible):
        assert isinstance(self, QgsRasterRendererWidget)
        for i in range(grid.count()):
            item = grid.itemAt(i)
            if isinstance(item, QLayout):
                s = ""
            elif isinstance(item, QWidgetItem):
                item.widget().setVisible(isVisible)
                item.widget().setParent(self)
            else:
                s = ""

    def setBandSelection(self, key):
        if key == 'default':
            bands = defaultBands(self.rasterLayer())
        else:
            colors = re.split('[ ,;:]', key)

            bands = [bandClosestToWavelength(self.rasterLayer(), c) for c in colors]

        n = min(len(bands), len(self.mBandComboBoxes))
        for i in range(n):
            cb = self.mBandComboBoxes[i]
            bandIndex = bands[i]
            if self.comboBoxWithNotSetItem(cb):
                cb.setCurrentIndex(bandIndex+1)
            else:
                cb.setCurrentIndex(bandIndex)


    def fixBandNames(self, comboBox):
        """
        Changes the QGIS default bandnames ("Band 001") to more meaning ful information including gdal.Dataset.Descriptions.
        :param widget:
        :param comboBox:
        """
        assert isinstance(self, QgsRasterRendererWidget)
        if type(comboBox) is QComboBox:
            bandNames = displayBandNames(self.rasterLayer())
            for i in range(comboBox.count()):
                # text = cb.itemText(i)
                if i > 0:
                    comboBox.setItemText(i, bandNames[i - 1])
        else:
            raise NotImplementedError()


class SingleBandGrayRendererWidget(QgsSingleBandGrayRendererWidget, RendererWidgetModifications):
    @staticmethod
    def create(layer, extent):
        return SingleBandGrayRendererWidget(layer, extent)

    def __init__(self, layer, extent):
        super(SingleBandGrayRendererWidget, self).__init__(layer, extent)

        self.modifyGridLayout()
        self.mGrayBandSlider = QSlider(Qt.Horizontal)
        self.mBandComboBoxes.append(self.mGrayBandComboBox)
        self.fixBandNames(self.mGrayBandComboBox)
        self.connectSliderWithBandComboBox(self.mGrayBandSlider, self.mGrayBandComboBox)

        self.mBtnBar = QFrame()
        self.initActionButtons()

        self.gridLayout.addWidget(self.mGrayBandLabel, 0, 0)
        self.gridLayout.addWidget(self.mBtnBar, 0, 1, 1, 4, Qt.AlignLeft)

        self.gridLayout.addWidget(self.mGrayBandSlider, 1, 1, 1, 2)
        self.gridLayout.addWidget(self.mGrayBandComboBox, 1, 3,1,2)

        self.gridLayout.addWidget(self.label, 2, 0)
        self.gridLayout.addWidget(self.mGradientComboBox, 2, 1, 1, 4)

        self.gridLayout.addWidget(self.mMinLabel, 3, 1)
        self.gridLayout.addWidget(self.mMinLineEdit, 3, 2)
        self.gridLayout.addWidget(self.mMaxLabel, 3, 3)
        self.gridLayout.addWidget(self.mMaxLineEdit, 3, 4)

        self.gridLayout.addWidget(self.mContrastEnhancementLabel, 4, 0)
        self.gridLayout.addWidget(self.mContrastEnhancementComboBox, 4, 1, 1 ,4)
        self.gridLayout.setSpacing(2)

        self.setLayoutItemVisibility(self.gridLayout, True)

        self.mDefaultRenderer = layer.renderer()


    def initActionButtons(self):
            wl, wlu = parseWavelength(self.rasterLayer())
            self.wavelengths = wl
            self.wavelengthUnit = wlu

            self.mBtnBar.setLayout(QHBoxLayout())
            self.mBtnBar.layout().addStretch()
            self.mBtnBar.layout().setContentsMargins(0, 0, 0, 0)
            self.mBtnBar.layout().setSpacing(2)

            self.actionSetDefault = QAction('Default', None)
            self.actionSetRed = QAction('R', None)
            self.actionSetGreen = QAction('G', None)
            self.actionSetBlue = QAction('B', None)
            self.actionSetNIR = QAction('nIR', None)
            self.actionSetSWIR = QAction('swIR', None)

            self.actionSetDefault.triggered.connect(lambda: self.setBandSelection('default'))
            self.actionSetRed.triggered.connect(lambda: self.setBandSelection('R'))
            self.actionSetGreen.triggered.connect(lambda: self.setBandSelection('G'))
            self.actionSetBlue.triggered.connect(lambda: self.setBandSelection('B'))
            self.actionSetNIR.triggered.connect(lambda: self.setBandSelection('nIR'))
            self.actionSetSWIR.triggered.connect(lambda: self.setBandSelection('swIR'))


            def addBtnAction(action):
                btn = QToolButton()
                btn.setDefaultAction(action)
                self.mBtnBar.layout().addWidget(btn)
                self.insertAction(None, action)
                return btn

            self.btnDefault = addBtnAction(self.actionSetDefault)
            self.btnRed = addBtnAction(self.actionSetRed)
            self.btnGreen = addBtnAction(self.actionSetGreen)
            self.btnBlue = addBtnAction(self.actionSetRed)
            self.btnNIR = addBtnAction(self.actionSetNIR)
            self.btnSWIR = addBtnAction(self.actionSetSWIR)

            b = self.wavelengths is not None
            for a in [self.actionSetRed, self.actionSetGreen, self.actionSetBlue, self.actionSetNIR, self.actionSetSWIR]:
                a.setEnabled(b)



class SingleBandPseudoColorRendererWidget(QgsSingleBandPseudoColorRendererWidget, RendererWidgetModifications):
    @staticmethod
    def create(layer, extent):
        return SingleBandPseudoColorRendererWidget(layer, extent)

    def __init__(self, layer, extent):
        super(SingleBandPseudoColorRendererWidget, self).__init__(layer, extent)

        self.gridLayout = self.layout().children()[0]
        assert isinstance(self.gridLayout, QGridLayout)
        for i in range(self.gridLayout.count()):
            w = self.gridLayout.itemAt(i)
            w = w.widget()
            if isinstance(w, QWidget):
                setattr(self, w.objectName(), w)

        toReplace = [self.mBandComboBox,self.mMinLabel,self.mMaxLabel, self.mMinLineEdit, self.mMaxLineEdit ]
        for w in toReplace:
            self.gridLayout.removeWidget(w)
            w.setVisible(False)
        self.mBandSlider = QSlider(Qt.Horizontal)
        self.mBandComboBoxes.append(self.mBandComboBox)
        self.fixBandNames(self.mBandComboBox)
        self.connectSliderWithBandComboBox(self.mBandSlider, self.mBandComboBox)

        self.mBtnBar = QFrame()
        self.initActionButtons()
        grid = QGridLayout()
        grid.addWidget(self.mBtnBar,0,0,1,4, Qt.AlignLeft)
        grid.addWidget(self.mBandSlider, 1,0, 1,2)
        grid.addWidget(self.mBandComboBox, 1,2, 1,2)
        grid.addWidget(self.mMinLabel, 2, 0)
        grid.addWidget(self.mMinLineEdit, 2, 1)
        grid.addWidget(self.mMaxLabel, 2, 2)
        grid.addWidget(self.mMaxLineEdit, 2, 3)
        #grid.setContentsMargins(2, 2, 2, 2, )
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(2, 0)
        grid.setColumnStretch(3, 2)
        grid.setSpacing(2)
        self.gridLayout.addItem(grid, 0,1,2,4)
        self.gridLayout.setSpacing(2)
        self.setLayoutItemVisibility(grid, True)


    def initActionButtons(self):
            wl, wlu = parseWavelength(self.rasterLayer())
            self.wavelengths = wl
            self.wavelengthUnit = wlu

            self.mBtnBar.setLayout(QHBoxLayout())
            self.mBtnBar.layout().addStretch()
            self.mBtnBar.layout().setContentsMargins(0, 0, 0, 0)
            self.mBtnBar.layout().setSpacing(2)

            self.actionSetDefault = QAction('Default', None)
            self.actionSetRed = QAction('R', None)
            self.actionSetGreen = QAction('G', None)
            self.actionSetBlue = QAction('B', None)
            self.actionSetNIR = QAction('nIR', None)
            self.actionSetSWIR = QAction('swIR', None)

            self.actionSetDefault.triggered.connect(lambda: self.setBandSelection('default'))
            self.actionSetRed.triggered.connect(lambda: self.setBandSelection('R'))
            self.actionSetGreen.triggered.connect(lambda: self.setBandSelection('G'))
            self.actionSetBlue.triggered.connect(lambda: self.setBandSelection('B'))
            self.actionSetNIR.triggered.connect(lambda: self.setBandSelection('nIR'))
            self.actionSetSWIR.triggered.connect(lambda: self.setBandSelection('swIR'))


            def addBtnAction(action):
                btn = QToolButton()
                btn.setDefaultAction(action)
                self.mBtnBar.layout().addWidget(btn)
                self.insertAction(None, action)
                return btn

            self.btnDefault = addBtnAction(self.actionSetDefault)
            self.btnRed = addBtnAction(self.actionSetRed)
            self.btnGreen = addBtnAction(self.actionSetGreen)
            self.btnBlue = addBtnAction(self.actionSetRed)
            self.btnNIR = addBtnAction(self.actionSetNIR)
            self.btnSWIR = addBtnAction(self.actionSetSWIR)

            b = self.wavelengths is not None
            for a in [self.actionSetRed, self.actionSetGreen, self.actionSetBlue, self.actionSetNIR, self.actionSetSWIR]:
                a.setEnabled(b)




class MultiBandColorRendererWidget(QgsMultiBandColorRendererWidget, RendererWidgetModifications):
    @staticmethod
    def create(layer, extent):
        return MultiBandColorRendererWidget(layer, extent)

    def __init__(self, layer, extent):
        super(MultiBandColorRendererWidget, self).__init__(layer, extent)

        self.modifyGridLayout()

        self.mRedBandSlider = QSlider(Qt.Horizontal)
        self.mGreenBandSlider = QSlider(Qt.Horizontal)
        self.mBlueBandSlider = QSlider(Qt.Horizontal)

        self.mBandComboBoxes.extend([self.mRedBandComboBox, self.mGreenBandComboBox, self.mBlueBandComboBox])
        self.mSliders = [self.mRedBandSlider, self.mGreenBandSlider, self.mBlueBandSlider]
        nb = self.rasterLayer().dataProvider().bandCount()
        for cbox, slider in zip(self.mBandComboBoxes, self.mSliders):
            self.connectSliderWithBandComboBox(slider, cbox)


        self.fixBandNames(self.mRedBandComboBox)
        self.fixBandNames(self.mGreenBandComboBox)
        self.fixBandNames(self.mBlueBandComboBox)

        self.mBtnBar = QFrame()
        self.mBtnBar.setLayout(QHBoxLayout())
        self.initActionButtons()
        self.mBtnBar.layout().addStretch()
        self.mBtnBar.layout().setContentsMargins(0, 0, 0, 0)
        self.mBtnBar.layout().setSpacing(2)

        #self.gridLayout.deleteLater()
#        self.gridLayout = newGrid
        self.gridLayout.addWidget(self.mBtnBar, 0, 1, 1, 3)
        self.gridLayout.addWidget(self.mRedBandLabel, 1, 0)
        self.gridLayout.addWidget(self.mRedBandSlider, 1, 1)
        self.gridLayout.addWidget(self.mRedBandComboBox, 1, 2)
        self.gridLayout.addWidget(self.mRedMinLineEdit, 1, 3)
        self.gridLayout.addWidget(self.mRedMaxLineEdit, 1, 4)

        self.gridLayout.addWidget(self.mGreenBandLabel, 2, 0)
        self.gridLayout.addWidget(self.mGreenBandSlider, 2, 1)
        self.gridLayout.addWidget(self.mGreenBandComboBox, 2, 2)
        self.gridLayout.addWidget(self.mGreenMinLineEdit, 2, 3)
        self.gridLayout.addWidget(self.mGreenMaxLineEdit, 2, 4)

        self.gridLayout.addWidget(self.mBlueBandLabel, 3, 0)
        self.gridLayout.addWidget(self.mBlueBandSlider, 3, 1)
        self.gridLayout.addWidget(self.mBlueBandComboBox, 3, 2)
        self.gridLayout.addWidget(self.mBlueMinLineEdit, 3, 3)
        self.gridLayout.addWidget(self.mBlueMaxLineEdit, 3, 4)

        self.gridLayout.addWidget(self.mContrastEnhancementAlgorithmLabel, 4, 0, 1, 2)
        self.gridLayout.addWidget(self.mContrastEnhancementAlgorithmComboBox, 4, 2, 1, 3)

        self.setLayoutItemVisibility(self.gridLayout, True)


        self.mRedBandLabel.setText('R')
        self.mGreenBandLabel.setText('G')
        self.mBlueBandLabel.setText('B')

        self.mDefaultRenderer = layer.renderer()

        self.minMaxWidget().resizeEvent = self.onMinMaxResize

    def onMinMaxResize(self, resizeEvent:QResizeEvent):

        s = ""



    def initActionButtons(self):

        wl, wlu = parseWavelength(self.rasterLayer())
        self.wavelengths = wl
        self.wavelengthUnit = wlu

        self.actionSetDefault = QAction('Default', None)
        self.actionSetTrueColor = QAction('RGB', None)
        self.actionSetCIR = QAction('nIR', None)
        self.actionSet453 = QAction('swIR', None)

        self.actionSetDefault.triggered.connect(lambda: self.setBandSelection('default'))
        self.actionSetTrueColor.triggered.connect(lambda: self.setBandSelection('R,G,B'))
        self.actionSetCIR.triggered.connect(lambda: self.setBandSelection('nIR,R,G'))
        self.actionSet453.triggered.connect(lambda: self.setBandSelection('nIR,swIR,R'))


        def addBtnAction(action):
            btn = QToolButton()
            btn.setDefaultAction(action)
            self.mBtnBar.layout().addWidget(btn)
            self.insertAction(None, action)
            return btn

        self.btnDefault = addBtnAction(self.actionSetDefault)
        self.btnTrueColor = addBtnAction(self.actionSetTrueColor)
        self.btnCIR = addBtnAction(self.actionSetCIR)
        self.btn453 = addBtnAction(self.actionSet453)

        b = self.wavelengths is not None
        for a in [self.actionSetCIR, self.actionSet453, self.actionSetTrueColor]:
            a.setEnabled(b)



class MapLayerModel(QgsMapLayerModel):

    def __init__(self, *args, **kwds):
        super(MapLayerModel, self).__init__(*args, **kwds)

    def data(self, index, role):
        assert isinstance(index, QModelIndex)
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            s = ""
        else:

            return super(MapLayerModel, self).data(index, role)


class RasterLayerProperties(QgsOptionsDialogBase, loadUI('rasterlayerpropertiesdialog.ui')):
    def __init__(self, lyr, canvas, parent=None):
        """Constructor."""
        title = 'RasterLayerProperties'
        super(RasterLayerProperties, self).__init__(title, parent, Qt.Dialog, settings=None)
        #super(RasterLayerProperties, self).__init__(parent, Qt.Dialog)

        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use auto connect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.initOptionsBase(False, title)
        #self.restoreOptionsBaseUi('TITLE')
        self.mRasterLayer = lyr
        self.mRendererWidget = None

        if not isinstance(canvas, QgsMapCanvas):
            canvas = QgsMapCanvas(self)
            canvas.setVisible(False)
            canvas.setLayers([lyr])
            canvas.setExtent(canvas.fullExtent())
        self.canvas = canvas

        self.oldStyle = self.mRasterLayer.styleManager().style(self.mRasterLayer.styleManager().currentStyle())

        self.accepted.connect(self.apply)
        self.rejected.connect(self.onCancel)
        self.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.apply)
        #connect controls

        self.initOptsGeneral()
        self.initOptsStyle()
        self.initOptsTransparency()
        self.initOptsMetadata()

    def setRendererWidget(self, rendererName:str):
        pass


    def initOptsGeneral(self):
        rl = self.mRasterLayer

        assert isinstance(rl, QgsRasterLayer)
        dp = rl.dataProvider()
        name = rl.name()
        if name == '':
            name = os.path.basename(rl.source())

        self.tb_layername.setText(name)
        self.tb_layersource.setText(rl.source())

        self.tb_columns.setText('{}'.format(dp.xSize()))
        self.tb_rows.setText('{}'.format(dp.ySize()))
        self.tb_bands.setText('{}'.format(dp.bandCount()))

        #mapUnits = ['m','km','ft','nmi','yd','mi','deg','ukn']
        #mapUnit = rl.crs().mapUnits()
        #mapUnit = mapUnits[mapUnit] if mapUnit < len(mapUnits) else 'ukn'
        mapUnit = QgsUnitTypes.toString(rl.crs().mapUnits())

        self.tb_pixelsize.setText('{0}{2} x {1}{2}'.format(rl.rasterUnitsPerPixelX(),rl.rasterUnitsPerPixelY(), mapUnit))
        self.tb_nodata.setText('{}'.format(dp.sourceNoDataValue(1)))


        se = SpatialExtent.fromLayer(rl)
        pt2str = lambda xy: '{} ; {}'.format(xy[0], xy[1])
        self.tb_upperLeft.setText(pt2str(se.upperLeft()))
        self.tb_upperRight.setText(pt2str(se.upperRight()))
        self.tb_lowerLeft.setText(pt2str(se.lowerLeft()))
        self.tb_lowerRight.setText(pt2str(se.lowerRight()))

        self.tb_width.setText('{} {}'.format(se.width(), mapUnit))
        self.tb_height.setText('{} {}'.format(se.height(), mapUnit))
        self.tb_center.setText(pt2str((se.center().x(), se.center().y())))

        self.mCrsSelector.setCrs(self.mRasterLayer.crs())
        s = ""


    def onCurrentRendererWidgetChanged(self, *args):
        self.mRendererStackedWidget
        assert isinstance(self.mRendererStackedWidget, QStackedWidget)
        cw = self.mRendererStackedWidget.currentWidget()

        assert isinstance(cw, QgsRasterRendererWidget)
        cw.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        cw.adjustSize()
        self.mRendererStackedWidget.adjustSize()



    def initOptsStyle(self):


        self.mRendererStackedWidget.currentChanged.connect(self.onCurrentRendererWidgetChanged)

        self.mRenderTypeComboBox.setModel(RASTERRENDERER_CREATE_FUNCTIONSV2)
        renderer = self.mRasterLayer.renderer()

        for func in RASTERRENDERER_CREATE_FUNCTIONSV2.optionValues():
            extent = self.canvas.extent()
            w = func(self.mRasterLayer, extent)
            w.setMapCanvas(self.canvas)
            #w.sizePolicy().setVerticalPolicy(QSizePolicy.Maximum)
            assert isinstance(w, QgsRasterRendererWidget)
            minMaxWidget = w.minMaxWidget()
            if isinstance(minMaxWidget, QgsRasterMinMaxWidget):
                minMaxWidget.setCollapsed(False)
            w.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            self.mRendererStackedWidget.addWidget(w)
            f2 = getattr(w, 'setFromRenderer', None)
            if f2:
                f2(renderer)




    def initOptsTransparency(self):

        r = self.mRasterLayer.renderer()
        if isinstance(r, QgsRasterRenderer):
            self.sliderOpacity.setValue(r.opacity()*100)


        def updateOpactiyText():
            self.lblTransparencyPercent.setText(r'{}%'.format(self.sliderOpacity.value()))

        self.sliderOpacity.valueChanged.connect(updateOpactiyText)
        updateOpactiyText()

    def initOptsMetadata(self):

        s = ""



    def onCancel(self):
        #restore style
        if self.oldStyle.xmlData() != self.mRasterLayer.styleManager().style(
                self.mRasterLayer.styleManager().currentStyle()
        ).xmlData():

            s = ""
        self.setResult(QDialog.Rejected)

    def apply(self):

        mRendererWidget = self.mRendererStackedWidget.currentWidget()
        if isinstance(mRendererWidget, QgsRasterRendererWidget):
            mRendererWidget.doComputations()
            renderer = mRendererWidget.renderer()
            assert isinstance(renderer, QgsRasterRenderer)
            renderer.setOpacity(self.sliderOpacity.value() / 100.)
            self.mRasterLayer.setRenderer(renderer)
            self.mRasterLayer.triggerRepaint()
            self.setResult(QDialog.Accepted)
        s  =""




class VectorLayerProperties(QgsOptionsDialogBase, loadUI('vectorlayerpropertiesdialog.ui')):

    def __init__(self, lyr, canvas, parent=None, fl=Qt.Widget):
        super(VectorLayerProperties, self).__init__("VectorLayerProperties", parent, fl)
        title = "Layer Properties - {}".format(lyr.name())
        self.restoreOptionsBaseUi(title)
        self.setupUi(self)
        self.initOptionsBase(False, title)
        self.mRendererDialog = None
        assert isinstance(lyr, QgsVectorLayer)
        assert isinstance(canvas, QgsMapCanvas)
        self.mLayer = lyr
        self.mCanvas = canvas
        self.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.syncToLayer)

        self.pbnQueryBuilder.clicked.connect(self.on_pbnQueryBuilder_clicked)
        self.accepted.connect(self.syncToLayer)

        self.rejected.connect(self.onCancel)
        self.syncFromLayer()

    def onCancel(self):
        pass

    def syncFromLayer(self):
        lyr = self.mLayer
        if isinstance(lyr, QgsVectorLayer):
            self.mLayerOrigNameLineEdit.setText(lyr.name())
            self.txtLayerSource.setText(lyr.publicSource())
            gtype = ['Point','Line','Polygon','Unknown','Undefined'][lyr.geometryType()]
            self.txtGeometryType.setText(gtype)
            self.txtnFeatures.setText('{}'.format(self.mLayer.featureCount()))
            self.txtnFields.setText('{}'.format(self.mLayer.fields().count()))

            self.mCrsSelector.setCrs(lyr.crs())

            self.txtSubsetSQL.setText(self.mLayer.subsetString())
            self.txtSubsetSQL.setEnabled(False)


        self.updateSymbologyPage()

        pass


    def syncToLayer(self):

        if isinstance(self.mRendererDialog, QgsRendererPropertiesDialog):
            self.mRendererDialog.apply()

        if self.txtSubsetSQL.toPlainText() != self.mLayer.subsetString():
            self.mLayer.setSubsetString(self.txtSubsetSQL.toPlainText())

        self.mLayer.triggerRepaint()
        pass

    def on_pbnQueryBuilder_clicked(self):
        qb = QgsQueryBuilder(self.mLayer, self)
        qb.setSql(self.txtSubsetSQL.toPlainText())

        if qb.exec_():
            self.txtSubsetSQL.setText(qb.sql())

    def updateSymbologyPage(self):

        while self.widgetStackRenderers.count() > 0:
            self.widgetStackRenderers.removeWidget(self.widgetStackRenderers.widget(0))

        self.mRendererDialog = None
        if self.mLayer.renderer():
            self.mRendererDialog = QgsRendererPropertiesDialog(self.mLayer, QgsStyle.defaultStyle(), True, self)
            self.mRendererDialog.setDockMode(False)
            self.mRendererDialog.setMapCanvas(self.mCanvas)

            self.mRendererDialog.layout().setContentsMargins(0, 0, 0, 0)
            self.widgetStackRenderers.addWidget(self.mRendererDialog)
            self.widgetStackRenderers.setCurrentWidget(self.mRendererDialog)

            self.mOptsPage_Style.setEnabled(True)
        else:
            self.mOptsPage_Style.setEnabled(False)


def showLayerPropertiesDialog(layer, canvas, parent=None, modal=True):
    dialog = None

    if isinstance(layer, QgsRasterLayer):
        dialog = RasterLayerProperties(layer, canvas,parent=parent)
        #d.setSettings(QSettings())
    elif isinstance(layer, QgsVectorLayer):
        dialog = VectorLayerProperties(layer, canvas, parent=parent)
    else:
        assert NotImplementedError()

    if modal == True:
        dialog.setModal(True)
    else:
        dialog.setModal(False)

    result = dialog.exec_()
    return result

RASTERRENDERER_CREATE_FUNCTIONSV2 = OptionListModel()
RASTERRENDERER_CREATE_FUNCTIONSV2.addOption(Option(MultiBandColorRendererWidget.create, name='multibandcolor'))
RASTERRENDERER_CREATE_FUNCTIONSV2.addOption(Option(QgsMultiBandColorRendererWidget.create, name='multibandcolor (QGIS)'))
RASTERRENDERER_CREATE_FUNCTIONSV2.addOption(Option(QgsPalettedRendererWidget.create, name='paletted'))
RASTERRENDERER_CREATE_FUNCTIONSV2.addOption(Option(SingleBandGrayRendererWidget.create, name='singlegray'))
#RASTERRENDERER_CREATE_FUNCTIONSV2.addOption(Option(QgsSingleBandGrayRendererWidget.create, name='singlegray (QGIS)'))
RASTERRENDERER_CREATE_FUNCTIONSV2.addOption(Option(SingleBandPseudoColorRendererWidget.create, name='singlebandpseudocolor'))
#RASTERRENDERER_CREATE_FUNCTIONSV2.addOption(Option(QgsSingleBandPseudoColorRendererWidget.create, name='singlebandpseudocolor (QGIS)'))

