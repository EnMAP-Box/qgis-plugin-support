# autogenerated file. do not modify
from qgis.core import Qgis


#  Import old locations
from qgis.core import (QgsAction, QgsArcGisPortalUtils, QgsAttributeEditorElement, QgsEditFormConfig, QgsGpsInformation, QgsGradientFillSymbolLayer, QgsGraduatedSymbolRenderer, QgsLabeling, QgsLabelingEngineSettings, QgsMapLayerProxyModel, QgsMapLayerType, QgsPainting, QgsPalLayerSettings, QgsProject, QgsProviderMetadata, QgsRandomMarkerFillSymbolLayer, QgsRaster, QgsRasterFileWriter, QgsRasterLayer, QgsRelation, QgsSimpleMarkerSymbolLayerBase, QgsStringUtils, QgsTextFormat, QgsTextRenderer, QgsUnitTypes, QgsVectorFileWriter, QgsWkbTypes)
from qgis.gui import (QgsActionMenu, QgsMapLayerAction)

#  API Switches
QGIS_ACTIONTYPE = Qgis.ActionType if Qgis.versionInt() >= 33000 else QgsActionMenu.ActionType
QGIS_ANGLEUNIT = Qgis.AngleUnit if Qgis.versionInt() >= 33000 else QgsUnitTypes.AngleUnit
QGIS_ARCGISRESTSERVICETYPE = Qgis.ArcGisRestServiceType if Qgis.versionInt() >= 32600 else QgsArcGisPortalUtils.ItemType
QGIS_AREAUNIT = Qgis.AreaUnit if Qgis.versionInt() >= 33000 else QgsUnitTypes.AreaUnit
QGIS_ATTRIBUTEACTIONTYPE = Qgis.AttributeActionType if Qgis.versionInt() >= 33000 else QgsAction.ActionType
QGIS_ATTRIBUTEEDITORTYPE = Qgis.AttributeEditorType if Qgis.versionInt() >= 33200 else QgsAttributeEditorElement.AttributeEditorType
QGIS_ATTRIBUTEFORMLAYOUT = Qgis.AttributeFormLayout if Qgis.versionInt() >= 33200 else QgsEditFormConfig.EditorLayout
QGIS_ATTRIBUTEFORMPYTHONINITCODESOURCE = Qgis.AttributeFormPythonInitCodeSource if Qgis.versionInt() >= 33200 else QgsEditFormConfig.PythonInitCodeSource
QGIS_ATTRIBUTEFORMSUPPRESSION = Qgis.AttributeFormSuppression if Qgis.versionInt() >= 33200 else QgsEditFormConfig.FeatureFormSuppress
QGIS_AVOIDINTERSECTIONSMODE = Qgis.AvoidIntersectionsMode if Qgis.versionInt() >= 32600 else QgsProject.AvoidIntersectionsMode
QGIS_BLENDMODE = Qgis.BlendMode if Qgis.versionInt() >= 33000 else QgsPainting.BlendMode
QGIS_CAPITALIZATION = Qgis.Capitalization if Qgis.versionInt() >= 32400 else QgsStringUtils.Capitalization
QGIS_DISTANCEUNIT = Qgis.DistanceUnit if Qgis.versionInt() >= 33000 else QgsUnitTypes.DistanceUnit
QGIS_DISTANCEUNITTYPE = Qgis.DistanceUnitType if Qgis.versionInt() >= 33000 else QgsUnitTypes.DistanceUnitType
QGIS_FEATURESYMBOLOGYEXPORT = Qgis.FeatureSymbologyExport if Qgis.versionInt() >= 33200 else QgsVectorFileWriter.SymbologyExport
QGIS_FILEFILTERTYPE = Qgis.FileFilterType if Qgis.versionInt() >= 33200 else QgsProviderMetadata.FilterType
QGIS_GEOMETRYTYPE = Qgis.GeometryType if Qgis.versionInt() >= 33000 else QgsWkbTypes.GeometryType
QGIS_GPSFIXSTATUS = Qgis.GpsFixStatus if Qgis.versionInt() >= 33000 else QgsGpsInformation.FixStatus
QGIS_GRADIENTCOLORSOURCE = Qgis.GradientColorSource if Qgis.versionInt() >= 32400 else QgsGradientFillSymbolLayer.GradientColorType
QGIS_GRADIENTSPREAD = Qgis.GradientSpread if Qgis.versionInt() >= 32400 else QgsGradientFillSymbolLayer.GradientSpread
QGIS_GRADIENTTYPE = Qgis.GradientType if Qgis.versionInt() >= 32400 else QgsGradientFillSymbolLayer.GradientType
QGIS_GRADUATEDMETHOD = Qgis.GraduatedMethod if Qgis.versionInt() >= 32600 else QgsGraduatedSymbolRenderer.GraduatedMethod
QGIS_LABELLINEPLACEMENTFLAG = Qgis.LabelLinePlacementFlag if Qgis.versionInt() >= 33200 else QgsLabeling.LinePlacementFlag
QGIS_LABELMULTILINEALIGNMENT = Qgis.LabelMultiLineAlignment if Qgis.versionInt() >= 32600 else QgsPalLayerSettings.MultiLineAlign
QGIS_LABELOFFSETTYPE = Qgis.LabelOffsetType if Qgis.versionInt() >= 32600 else QgsPalLayerSettings.OffsetType
QGIS_LABELPLACEMENT = Qgis.LabelPlacement if Qgis.versionInt() >= 32600 else QgsPalLayerSettings.Placement
QGIS_LABELPLACEMENTENGINEVERSION = Qgis.LabelPlacementEngineVersion if Qgis.versionInt() >= 33000 else QgsLabelingEngineSettings.PlacementEngineVersion
QGIS_LABELPOLYGONPLACEMENTFLAG = Qgis.LabelPolygonPlacementFlag if Qgis.versionInt() >= 33200 else QgsLabeling.PolygonPlacementFlag
QGIS_LABELPREDEFINEDPOINTPOSITION = Qgis.LabelPredefinedPointPosition if Qgis.versionInt() >= 32600 else QgsPalLayerSettings.PredefinedPointPosition
QGIS_LABELQUADRANTPOSITION = Qgis.LabelQuadrantPosition if Qgis.versionInt() >= 32600 else QgsPalLayerSettings.QuadrantPosition
QGIS_LABELINGFLAG = Qgis.LabelingFlag if Qgis.versionInt() >= 33000 else QgsLabelingEngineSettings.Flag
QGIS_LAYERFILTER = Qgis.LayerFilter if Qgis.versionInt() >= 33400 else QgsMapLayerProxyModel.Filter
QGIS_LAYERTYPE = Qgis.LayerType if Qgis.versionInt() >= 33000 else QgsMapLayerType
QGIS_LAYOUTUNIT = Qgis.LayoutUnit if Qgis.versionInt() >= 33000 else QgsUnitTypes.LayoutUnit
QGIS_LAYOUTUNITTYPE = Qgis.LayoutUnitType if Qgis.versionInt() >= 33000 else QgsUnitTypes.LayoutUnitType
QGIS_MAPLAYERACTIONFLAG = Qgis.MapLayerActionFlag if Qgis.versionInt() >= 33000 else QgsMapLayerAction.Flag
QGIS_MAPLAYERACTIONTARGET = Qgis.MapLayerActionTarget if Qgis.versionInt() >= 33000 else QgsMapLayerAction.Target
QGIS_MARKERSHAPE = Qgis.MarkerShape if Qgis.versionInt() >= 32400 else QgsSimpleMarkerSymbolLayerBase.Shape
QGIS_POINTCOUNTMETHOD = Qgis.PointCountMethod if Qgis.versionInt() >= 32400 else QgsRandomMarkerFillSymbolLayer.CountMethod
QGIS_PROJECTFILEFORMAT = Qgis.ProjectFileFormat if Qgis.versionInt() >= 32600 else QgsProject.FileFormat
QGIS_PROJECTREADFLAG = Qgis.ProjectReadFlag if Qgis.versionInt() >= 32600 else QgsProject.ReadFlag
QGIS_RASTERBUILDPYRAMIDOPTION = Qgis.RasterBuildPyramidOption if Qgis.versionInt() >= 33000 else QgsRaster.RasterBuildPyramids
QGIS_RASTERCOLORINTERPRETATION = Qgis.RasterColorInterpretation if Qgis.versionInt() >= 33000 else QgsRaster.ColorInterpretation
QGIS_RASTERDRAWINGSTYLE = Qgis.RasterDrawingStyle if Qgis.versionInt() >= 33000 else QgsRaster.DrawingStyle
QGIS_RASTEREXPORTTYPE = Qgis.RasterExportType if Qgis.versionInt() >= 33200 else QgsRasterFileWriter.Mode
QGIS_RASTERFILEWRITERRESULT = Qgis.RasterFileWriterResult if Qgis.versionInt() >= 33200 else QgsRasterFileWriter.WriterError
QGIS_RASTERIDENTIFYFORMAT = Qgis.RasterIdentifyFormat if Qgis.versionInt() >= 33000 else QgsRaster.IdentifyFormat
QGIS_RASTERLAYERTYPE = Qgis.RasterLayerType if Qgis.versionInt() >= 33000 else QgsRasterLayer.LayerType
QGIS_RASTERPYRAMIDFORMAT = Qgis.RasterPyramidFormat if Qgis.versionInt() >= 33000 else QgsRaster.RasterPyramidsFormat
QGIS_RELATIONSHIPSTRENGTH = Qgis.RelationshipStrength if Qgis.versionInt() >= 32800 else QgsRelation.RelationStrength
QGIS_RELATIONSHIPTYPE = Qgis.RelationshipType if Qgis.versionInt() >= 32800 else QgsRelation.RelationType
QGIS_RENDERUNIT = Qgis.RenderUnit if Qgis.versionInt() >= 33000 else QgsUnitTypes.RenderUnit
QGIS_SYMBOLCOORDINATEREFERENCE = Qgis.SymbolCoordinateReference if Qgis.versionInt() >= 32400 else QgsGradientFillSymbolLayer.GradientCoordinateMode
QGIS_SYSTEMOFMEASUREMENT = Qgis.SystemOfMeasurement if Qgis.versionInt() >= 33000 else QgsUnitTypes.SystemOfMeasurement
QGIS_TEMPORALUNIT = Qgis.TemporalUnit if Qgis.versionInt() >= 33000 else QgsUnitTypes.TemporalUnit
QGIS_TEXTCOMPONENT = Qgis.TextComponent if Qgis.versionInt() >= 32800 else QgsTextRenderer.TextPart
QGIS_TEXTHORIZONTALALIGNMENT = Qgis.TextHorizontalAlignment if Qgis.versionInt() >= 32800 else QgsTextRenderer.HAlignment
QGIS_TEXTLAYOUTMODE = Qgis.TextLayoutMode if Qgis.versionInt() >= 32800 else QgsTextRenderer.DrawMode
QGIS_TEXTORIENTATION = Qgis.TextOrientation if Qgis.versionInt() >= 32800 else QgsTextFormat.TextOrientation
QGIS_TEXTVERTICALALIGNMENT = Qgis.TextVerticalAlignment if Qgis.versionInt() >= 32800 else QgsTextRenderer.VAlignment
QGIS_UNITTYPE = Qgis.UnitType if Qgis.versionInt() >= 33000 else QgsUnitTypes.UnitType
QGIS_UPSIDEDOWNLABELHANDLING = Qgis.UpsideDownLabelHandling if Qgis.versionInt() >= 32600 else QgsPalLayerSettings.UpsideDownLabels
QGIS_VOLUMEUNIT = Qgis.VolumeUnit if Qgis.versionInt() >= 33000 else QgsUnitTypes.VolumeUnit

QGIS_WKBTYPE = Qgis.WkbType if Qgis.versionInt() >= 33000 else QgsWkbTypes.Type
