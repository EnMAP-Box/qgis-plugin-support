# noinspection PyPep8Naming
import datetime
import unittest
from typing import Tuple

from qgis.PyQt.QtWidgets import QGridLayout
from qgis.PyQt.QtWidgets import QWidget
from qgis.core import QgsProject, QgsProcessingParameterRasterLayer, \
    QgsProcessingContext, QgsProcessingRegistry, QgsApplication
from qgis.core import QgsVectorLayer
from qgis.gui import QgsGui, QgsProcessingParameterWidgetContext, QgsProcessingGui, QgsProcessingContextGenerator, \
    QgsProcessingAlgorithmDialogBase
from qgis.gui import QgsMapCanvas, QgsDualView
from qgis.gui import QgsProcessingGuiRegistry
from qps.speclib.core import profile_field_list
from qps.speclib.core.spectralprofile import SpectralSetting
from qps.speclib.gui.spectrallibrarywidget import SpectralLibraryWidget
from qps.speclib.gui.spectralprocessingdialog import SpectralProcessingDialog, \
    SpectralProcessingRasterLayerWidgetWrapper
from qps.testing import TestObjects, TestCaseBase, ExampleAlgorithmProvider, start_app

start_app()


class SpectralProcessingTests(TestCaseBase):

    def initProcessingRegistry(self) -> Tuple[QgsProcessingRegistry, QgsProcessingGuiRegistry]:
        procReg = QgsApplication.instance().processingRegistry()
        procGuiReg: QgsProcessingGuiRegistry = QgsGui.processingGuiRegistry()
        assert isinstance(procReg, QgsProcessingRegistry)

        # provider_names = [p.name() for p in procReg.providers()]

        return procReg, procGuiReg

    def algorithmProviderTesting(self) -> 'ExampleAlgorithmProvider':
        return QgsApplication.instance().processingRegistry().providerById(ExampleAlgorithmProvider.NAME.lower())

    def test_dualview(self):

        n_features = 5000
        # sl = TestObjects.createVectorLayer(n_features=n_features)
        sl: QgsVectorLayer = TestObjects.createSpectralLibrary(n_features, n_bands=[177])
        self.assertEqual(sl.featureCount(), n_features)
        c = QgsMapCanvas()
        if True:
            dv = QgsDualView()
            dv.init(sl, c, loadFeatures=True)
        sl.startEditing()
        fids = sl.allFeatureIds()
        sl.selectByIds(fids[-2500:])
        n_to_del = len(sl.selectedFeatureIds())
        t0 = datetime.datetime.now()
        context = QgsVectorLayer.DeleteContext(cascade=True, project=QgsProject.instance())
        sl.beginEditCommand('Delete features')
        success, n_del = sl.deleteSelectedFeatures(context)
        sl.endEditCommand()
        assert success
        print(f'Required {datetime.datetime.now() - t0} to delete {n_del} features')
        # self.showGui(dv)

    def test_algwidget(self):
        self.initProcessingRegistry()
        from qps.speclib.core.spectrallibraryrasterdataprovider import registerDataProvider
        registerDataProvider()
        n_bands = [256]
        n_features = 20
        speclib = TestObjects.createSpectralLibrary(n=n_features, n_bands=n_bands)
        speclib: QgsVectorLayer

        speclib.startEditing()
        procw = SpectralProcessingDialog(speclib=speclib)
        # procw.setSpeclib(speclib)
        reg: QgsProcessingRegistry = QgsApplication.instance().processingRegistry()
        alg1 = reg.algorithmById('gdal:rearrange_bands')
        alg2 = reg.algorithmById('native:rescaleraster')

        procw.setAlgorithm(alg2)
        self.showGui(procw)

    @unittest.skipIf(TestCaseBase.runsInCI(), 'Blocking dialog')
    def test_SpectralProcessingWidget2(self):
        self.initProcessingRegistry()
        from qps.speclib.core.spectrallibraryrasterdataprovider import registerDataProvider
        registerDataProvider()
        n_bands = [256, 13]
        n_features = 20
        speclib = TestObjects.createSpectralLibrary(n=n_features, n_bands=n_bands)
        speclib: QgsVectorLayer

        slw = SpectralLibraryWidget(speclib=speclib)
        pFields = profile_field_list(speclib)

        speclib.startEditing()
        procw = SpectralProcessingDialog()
        procw.setSpeclib(speclib)
        reg: QgsProcessingRegistry = QgsApplication.instance().processingRegistry()
        alg1 = reg.algorithmById('gdal:rearrange_bands')
        alg2 = reg.algorithmById('native:rescaleraster')
        procw.setAlgorithm(alg2)
        wrapper = procw.processingModelWrapper()
        cbInputField = wrapper.parameterWidget('INPUT')
        cbInputField.setCurrentIndex(1)
        currentInputFieldName = cbInputField.currentText()

        cb2 = wrapper.outputWidget('OUTPUT')
        cb2.setCurrentText('newfield')

        procw.runAlgorithm(fail_fast=True)
        tempFiles = procw.temporaryRaster()
        for file in tempFiles:
            setting = SpectralSetting.fromRasterLayer(file)
            assert setting.xUnit() not in [None, '']
        self.assertTrue(True)
        self.showGui([slw, procw])

    def test_SpectralProcessingRasterLayerWidgetWrapper(self):

        parameters = [
            QgsProcessingParameterRasterLayer('rasterlayer'),

        ]

        gridLayout = QGridLayout()

        layers = [TestObjects.createRasterLayer(),
                  TestObjects.createRasterLayer(),
                  TestObjects.createVectorLayer()]

        class ContextGenerator(QgsProcessingContextGenerator):

            def __init__(self, context):
                super().__init__()
                self.processing_context = context

            def processingContext(self):
                return self.processing_context

        project = QgsProject()
        project.addMapLayers(layers)
        widget_context = QgsProcessingParameterWidgetContext()
        widget_context.setProject(project)
        processing_context = QgsProcessingContext()
        context_generator = ContextGenerator(processing_context)
        parameters_generator = None

        def onValueChanged(*args):
            print(args)

        wrappers = dict()
        widgets = []
        for i, param in enumerate(parameters):
            wrapper = SpectralProcessingRasterLayerWidgetWrapper(param, QgsProcessingGui.Standard)
            wrapper.setWidgetContext(widget_context)
            wrapper.registerProcessingContextGenerator(context_generator)
            wrapper.registerProcessingParametersGenerator(parameters_generator)
            wrapper.widgetValueHasChanged.connect(onValueChanged)
            # store wrapper instance
            wrappers[param.name()] = wrapper
            label = wrapper.createWrappedLabel()
            # self.addParameterLabel(param, label)
            widget = wrapper.createWrappedWidget(processing_context)
            widgets.append((label, widget))
            gridLayout.addWidget(label, i, 0)
            gridLayout.addWidget(widget, i, 1)

        w = QWidget()
        w.setLayout(gridLayout)
        self.showGui(w)

    @unittest.skipIf(TestCaseBase.runsInCI(), 'Sandbox only')
    def test_dialog(self):
        class D(QgsProcessingAlgorithmDialogBase):
            def __init__(self, *args, **kwds):
                super().__init__(*args, **kwds)

        d = D()
        d.exec_()

    def test_SpectralLibraryWidget(self):
        self.initProcessingRegistry()

        from qps.speclib.core.spectrallibraryrasterdataprovider import registerDataProvider
        registerDataProvider()
        n_bands = [[256, 2500],
                   [123, 42]]
        n_features = 10
        speclib = TestObjects.createSpectralLibrary(n=n_features, n_bands=n_bands)
        speclib: QgsVectorLayer
        # speclib.selectByIds([1, 2, 3, 4])
        # speclib.startEditing()
        slw = SpectralLibraryWidget(speclib=speclib)
        self.showGui(slw)


if __name__ == '__main__':
    unittest.main(buffer=False)
