import typing

from PyQt5.QtCore import QVariant
from qgis.core import QgsEditorWidgetSetup

from qgis.core import QgsVectorLayer, QgsField, QgsFeature, QgsFields

from qps.speclib import EDITOR_WIDGET_REGISTRY_KEY


def create_profile_field(name: str, comment:str='') -> QgsField:
    """
    Creates a QgsField to store spectral profiles
    :param name: field name
    :param comment: field comment, optional
    :return: QgsField
    """
    field = QgsField(name=name, type=QVariant.ByteArray, comment=comment)
    setup = QgsEditorWidgetSetup(EDITOR_WIDGET_REGISTRY_KEY, {})
    field.setEditorWidgetSetup(setup)
    return field

def is_profile_field(field: QgsField) -> bool:
    return isinstance(field, QgsField) and field.editorWidgetSetup().type() == EDITOR_WIDGET_REGISTRY_KEY

def is_spectral_library()-> bool:
    pass

def has_profile_fields()-> bool:
    pass

def profile_fields(spectralLibrary: typing.Union[QgsFeature, QgsVectorLayer]) -> typing.List[QgsField]:
    """
    Returns the fields that contains values of SpectralProfiles
    :param spectralLibrary:
    :return:
    """
    fields = [f for f in spectralLibrary.fields() if
              f.type() == QVariant.ByteArray]
    if isinstance(spectralLibrary, QgsVectorLayer):
        fields = [f for f in fields if is_profile_field(f)]
    return fields

def profile_field_lookup(spectralLibrary: typing.Union[QgsFeature, QgsVectorLayer]) -> \
    typing.Dict[typing.Union[int, str], QgsField]:

    fields = profile_fields(spectralLibrary)
    D = {f.name(): f for f in fields}
    for f in fields:
        D[spectralLibrary.fields().lookupField(f.name())] = f
    return D

def profile_field_indices(spectralLibrary: typing.Union[QgsFeature, QgsVectorLayer]) -> typing.List[int]:
    return [spectralLibrary.fields().lookupField(f.name()) for f in profile_fields(spectralLibrary)]

def profile_field_names(spectralLibrary: typing.Union[QgsFeature, QgsVectorLayer]) -> typing.List[str]:
    return [f.name() for f in profile_fields(spectralLibrary)]


def first_profile_field_index(source: typing.Union[QgsFields, QgsFeature, QgsVectorLayer]) -> int:
    """
    Returns the 1st QByteArray field that can be used to store Spectral Profile data
    :param source:
    :return:
    """
    if isinstance(source, QgsVectorLayer):
        for f in profile_fields(source):
            return source.fields().lookupField(f.name())
    elif isinstance(source, QgsFeature):
        return first_profile_field_index(source.fields())
    elif isinstance(source, QgsFields):
        for f in source:
            if f.type() == QVariant.ByteArray:
                return source.lookupField(f.name())
    return -1


def field_index(source: typing.Union[QgsFields, QgsFeature, QgsVectorLayer], field: typing.Union[str, int, QgsField]) -> int:
    """
    Returns the field index as int, or -1, if not found
    :param source:
    :param field:
    :return:
    """
    if isinstance(field, int):
        return field

    idx = -1
    if isinstance(source, (QgsVectorLayer, QgsFeature)):
        fields = source.fields()
    assert isinstance(fields, QgsFields)
    if isinstance(field, QgsField):
        idx = fields.lookupField(field.name())
    elif isinstance(field, str):
        idx = fields.lookupField(field)

    return idx