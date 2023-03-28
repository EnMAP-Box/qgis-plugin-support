import os
import shutil
import unittest

from qgis.PyQt.QtWidgets import QDialog
from qgis.core import QgsProviderSublayerDetails, QgsApplication

from qps.subdatasets import SubDatasetLoadingTask, SubDatasetSelectionDialog
from qps.testing import TestCaseBase, TestObjects, start_app2

start_app2()


@unittest.skipIf(not TestObjects.repoDirGDAL(), 'Test requires GDAL repo testdata')
class TestSubDataSets(TestCaseBase):
    @unittest.skipIf(not TestObjects.repoDirGDAL(), 'Test requires GDAL repo testdata')
    def test_subdatasettask(self):

        dir_gdal = TestObjects.repoDirGDAL()
        sources = [
            dir_gdal / 'autotest/gdrivers/data/hdf5/groups.h5',
            dir_gdal / 'autotest/gdrivers/data/sentinel2/fake_l1c/S2A_OPER_PRD_MSIL1C.SAFE/S2A_OPER_MTD_SAFL1C.xml',
            dir_gdal / 'autotest/gdrivers/data/sentinel2/fake_l2a/S2A_USER_PRD_MSIL2A.SAFE/S2A_USER_MTD_SAFL2A.xml',
            dir_gdal / 'autotest/gdrivers/data/sentinel2/fake_l2a/S2A_USER_PRD_MSIL2A.SAFE/S2A_USER_MTD_SAFL2A.xml',
            dir_gdal / 'autotest/gdrivers/data/gpkg/50000_25000_uint16.gpkg.zip'
        ]
        for s in sources:
            self.assertTrue(s.is_file(), msg=str(s))

        task = SubDatasetLoadingTask(sources)
        task.run()
        for p, results in task.results().items():
            self.assertTrue(os.path.isfile(p))
            self.assertTrue(len(results) > 0)
            for r in results:
                self.assertIsInstance(r, QgsProviderSublayerDetails)

    @unittest.skipIf(not TestObjects.repoDirGDAL(), 'Test requires GDAL repo testdata')
    def test_subdatasetDialog(self):

        dir_gdal = TestObjects.repoDirGDAL()
        path_grps = dir_gdal / 'autotest/gdrivers/data/hdf5/groups.h5'
        path_grps2 = self.createTestOutputDirectory() / 'groups2.h5'
        if not path_grps2.is_file():
            shutil.copy(path_grps, path_grps2)
            self.assertTrue(path_grps2.is_file())

        sources = [
            path_grps,
            path_grps2,
            dir_gdal / 'autotest/gdrivers/data/sentinel2/fake_l1c/S2A_OPER_PRD_MSIL1C.SAFE/S2A_OPER_MTD_SAFL1C.xml',
            dir_gdal / 'autotest/gdrivers/data/sentinel2/fake_l2a/S2A_USER_PRD_MSIL2A.SAFE/S2A_USER_MTD_SAFL2A.xml',
            dir_gdal / 'autotest/gdrivers/data/sentinel2/fake_l2a/S2A_USER_PRD_MSIL2A.SAFE/S2A_USER_MTD_SAFL2A.xml',
            dir_gdal / 'autotest/gdrivers/data/gpkg/50000_25000_uint16.gpkg.zip/50000_25000_uint16.gpkg',
            dir_gdal / 'autotest/ogr/data/gpkg/domains.gpkg',
            dir_gdal / 'autotest/ogr/data/gpkg/poly.gpkg.zip',
        ]

        d = SubDatasetSelectionDialog()
        d.setFiles(sources)
        QgsApplication.processEvents()
        d.showMultiFiles(False)
        d.showMultiFiles(True)

        while len(QgsApplication.taskManager().tasks()) > 0:
            QgsApplication.processEvents()

        self.assertTrue(d.tvSubDatasets.model().rowCount() > 0)

        d.tvSubDatasets.selectRow(0)
        sublayers = d.selectedSublayerDetails()
        self.assertEqual(len(sublayers), 2)

        if not TestCaseBase.runsInCI():
            if d.exec() == QDialog.Accepted:
                sublayers = d.selectedSublayerDetails()


if __name__ == '__main__':
    unittest.main(buffer=False)
