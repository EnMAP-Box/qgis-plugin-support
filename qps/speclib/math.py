import collections
import typing
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import QIcon, QColor

from qgis.PyQt.QtWidgets import QPlainTextEdit, QWidget, QTableView, QLabel, QComboBox, \
    QHBoxLayout, QVBoxLayout, QSpacerItem, QMenu, QAction, QToolButton, QGridLayout
from qgis.core import QgsFeature
from qgis.gui import QgsCollapsibleGroupBox, QgsCodeEditorPython
import numpy as np
from .core import SpectralLibrary, SpectralProfile, speclibUiPath
from ..unitmodel import UnitConverterFunctionModel, BAND_INDEX, XUnitModel
from ..utils import loadUi

SpectralMathResult = collections.namedtuple('SpectralMathResult', ['x', 'y', 'x_unit', 'y_unit'])

class AbstractSpectralMathFunction(QObject):

    @staticmethod
    def is_valid_result(result: SpectralMathResult) -> bool:
        if not isinstance(result, SpectralMathResult):
            return False
        if not isinstance(result.x, (np.ndarray, list)):
            return False
        if not isinstance(result.y, (np.ndarray, list)):
            return False
        return True

    @staticmethod
    def applyFunctionStack(functionStack: typing.Iterable[typing.Optional['AbstractSpectralMathFunction']],
                           *args) -> SpectralMathResult:

        if isinstance(functionStack, AbstractSpectralMathFunction):
            functionStack = [functionStack]
        else:
            assert isinstance(functionStack, typing.Iterable)

        spectralMathResult, feature = AbstractSpectralMathFunction._unpack(*args)

        for f in functionStack:
            assert isinstance(f, AbstractSpectralMathFunction)

            spectralMathResult = f.apply(spectralMathResult, feature)
            if not AbstractSpectralMathFunction.is_valid_result(spectralMathResult):
                return None

        return spectralMathResult

    @staticmethod
    def _unpack(*args) -> typing.Tuple[SpectralMathResult, QgsFeature]:
        assert len(args) >= 1
        f = None
        if isinstance(args[-1], QgsFeature):
            f = args[-1]

        if isinstance(args[0], SpectralProfile):
            sp: SpectralProfile = args[0]
            x = sp.xValues()
            y = sp.yValues()
            x_unit = sp.xUnit()
            y_unit = sp.yUnit()
            f = sp
        elif isinstance(args[0], SpectralMathResult):
            return args[0], f
        elif len(args) == 4:
            x, y, x_unit, y_unit = args
        elif len(args) >= 5:
            x, y, x_unit, y_unit, f = args[:5]

        x = np.asarray(x)
        y = np.asarray(y)

        return SpectralMathResult(x=x, y=y, x_unit=x_unit, y_unit=y_unit), f

    def __init__(self, name: str = None):
        super().__init__()
        if name is None:
            name = self.__class__.__name__
        self.mError = None
        self.mName: str = name
        self.mHelp: str = None
        self.mIcon: QIcon = None
        self.mToolTip: str = None

    def id(self):
        self.__class__.__name__()

    def name(self) -> str:
        return self.mName

    def setName(self, name:str):
        assert isinstance(name, str)
        assert len(name) > 0
        self.mName = name

    def help(self) -> str:
        return self.mHelp

    def icon(self) -> QIcon:
        return self.mIcon

    def toolTip(self) -> str:
        return self.mToolTip

    sigChanged = pyqtSignal()

    def createWidget(self) -> QWidget:
        """
        Create a QWidget to configure this function
        :return:
        """
        return None

    def apply(self, spectralMathResult:SpectralMathResult, feature:QgsFeature) -> SpectralMathResult:
        """

        :param x: x values, e.g. wavelength or band indices
        :param y: y values, e.g. spectral values
        :param x_units: str, e.g. wavelength unit
        :param y_units: str
        :param feature: QgsFeature, e.g. with metadata
        :return: tuple with manipulated (x,y, x_units, y_units) or None if failed
        """
        return None


class XUnitConversion(AbstractSpectralMathFunction):

    def __init__(self, x_unit:str=BAND_INDEX, x_unit_model:XUnitModel=None):
        super().__init__()
        self.mTargetUnit = x_unit
        self.mUnitConverter = UnitConverterFunctionModel()

        if not isinstance(x_unit_model, XUnitModel):
            x_unit_model = XUnitModel()
        self.mUnitModel = x_unit_model

    def unitConverter(self) -> UnitConverterFunctionModel:
        return self.mUnitConverter

    def setTargetUnit(self, unit:str):
        self.mTargetUnit = unit

    def createWidget(self) -> QWidget:

        w = QWidget()
        l = QGridLayout()
        l.addWidget(QLabel('X Unit'), 0, 0)

        cb = QComboBox()
        cb.setModel(self.mUnitModel)
        cb.currentIndexChanged[str].connect(self.setTargetUnit)

        idx = self.mUnitModel.unitIndex(self.mTargetUnit)
        if idx.isValid():
            cb.setCurrentIndex(idx.row())
        l.addWidget(cb, 0, 1)
        w.setLayout(l)
        return w

    def apply(self, result:SpectralMathResult, feature: QgsFeature) -> SpectralMathResult:

        f = self.mUnitConverter.convertFunction(result.x_unit, self.mTargetUnit)
        if callable(f):
            x = f(result.x)
            return SpectralMathResult(x=x, y=result.y, x_unit=self.mTargetUnit, y_unit=result.y_unit)
        else:
            return None


class GenericSpectralMathFunction(AbstractSpectralMathFunction):

    def __init__(self):
        super().__init__()
        self.mExpression = None

    def setExpression(self, expression:str):
        changed = expression != self.mExpression
        self.mExpression = expression

        if changed:
            self.sigChanged.emit()

    def apply(self, spectralMathResult:SpectralMathResult, feature:QgsFeature) -> SpectralMathResult:
        self.mError = None

        if self.mExpression:
            values = spectralMathResult._asdict()

            try:
                exec(self.mExpression, values)
                return SpectralMathResult(x=values['x'], y=values['y'], x_unit=values['x_unit'], y_unit=values['y_unit'] )
            except Exception as ex:
                self.mError = str(ex)
                return None
        else:
            return spectralMathResult


    def createWidget(self) -> QgsCodeEditorPython:

        editor = QgsCodeEditorPython()
        editor.setTitle(self.name())
        editor.setText(self.mExpression)
        editor.textChanged.connect(lambda *args, e=editor: self.setExpression(e.text()))
        return editor


class SpectralMathFunctionModel(QAbstractTableModel):

    sigChanged = pyqtSignal()

    def __init__(self, *args, **kwds):
        super(SpectralMathFunctionModel, self).__init__(*args, **kwds)

        self.mFunctions: typing.List[AbstractSpectralMathFunction] = []
        self.mIsEnabled: typing.Dict[AbstractSpectralMathFunction, bool] = dict()

        self.mColumnNames = ['Steps']

    def __iter__(self):
        return iter(self.mFunctions)

    def __len__(self):
        return len(self.mFunctions)

    def validate(self, test: SpectralMathResult) -> bool:

        stack = self.functionStack()
        for f in self:
            f.mError = None

        result = AbstractSpectralMathFunction.applyFunctionStack(stack, test)
        roles = [Qt.DecorationRole, Qt.ToolTipRole]
        self.dataChanged.emit(
            self.createIndex(0, 0),
            self.createIndex(len(self)-1, 0),
            roles
        )
        return isinstance(result, SpectralMathResult)

    def headerData(self, i, orientation, role=None):

        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.mColumnNames[i]
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return f'{i+1}'
        return None

    def index(self, row:int, col:int, parent: QModelIndex=None):
        return self.createIndex(row, col, self.mFunctions[row])

    def functionStack(self) -> typing.List[AbstractSpectralMathFunction]:
        return [f for f in self.mFunctions if self.mIsEnabled.get(f, False)]

    def insertFunctions(self, index: int, functions: typing.Iterable[AbstractSpectralMathFunction]):
        n = len(functions)
        i0 = len(self)
        i1 = i0 + n - 1
        self.beginInsertRows(QModelIndex(), i0, i1)
        i = i0
        for i, f in enumerate(functions):
            f.sigChanged.connect(self.sigChanged)
            self.mFunctions.insert(i0 + i, f)
            self.mIsEnabled[f] = True
        self.endInsertRows()

    def addFunctions(self, functions):
        if isinstance(functions, AbstractSpectralMathFunction):
            functions = [functions]
        for f in functions:
            assert isinstance(f, AbstractSpectralMathFunction)
        self.insertFunctions(len(self), functions)

    def removeFunctions(self, functions):
        if isinstance(functions, AbstractSpectralMathFunction):
            functions = [functions]
        for f in functions:
            assert isinstance(f, AbstractSpectralMathFunction)
        for f in functions:
            if f in self.mFunctions:
                i = self.mFunctions.index(f)
                self.beginRemoveRows(QModelIndex(), i, i)
                self.mFunctions.remove(f)
                self.endRemoveRows()

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.mFunctions)

    def flags(self, index:QModelIndex):
        if not index.isValid():
            return Qt.NoItemFlags

        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEditable
        return flags

    def columnCount(self, parent=None, *args, **kwargs):
        return 1

    def setData(self, index:QModelIndex, value, role=None):

        if not index.isValid():
            return False
        f: AbstractSpectralMathFunction = self.mFunctions[index.row()]

        changed = False
        if role == Qt.CheckStateRole and index.column() == 0:
            self.mIsEnabled[f] = value == Qt.Checked
            changed = True
        if role == Qt.EditRole and index.column() == 0:
            name = str(value)
            if len(name) > 0:
                f.setName(name)
                changed = True
        if changed:
            self.dataChanged.emit(index, index)
        return changed

    def data(self, index:QModelIndex, role=None):
        if not index.isValid():
            return None

        f: AbstractSpectralMathFunction = self.mFunctions[index.row()]

        if role == Qt.DisplayRole:
            return f.name()

        if role == Qt.EditRole:
            return f.name()

        if role == Qt.DecorationRole:
            return f.icon()

        if role == Qt.ToolTipRole:
            if f.mError:
                return str(f.mError)
            else:
                return None
        if role == Qt.TextColorRole:
            if f.mError:
                return QColor('red')
            else:
                return None

        if role == Qt.CheckStateRole:
            if self.mIsEnabled.get(f, False) == True:
                return Qt.Checked
            else:
                return Qt.Unchecked

        if role == Qt.UserRole:
            return f

        return None


class SpectralMathFunctionTableView(QTableView):

    def __init__(self, *args, **kwds):

        super().__init__(*args, **kwds)


class SpectralMathWidget(QgsCollapsibleGroupBox):
    sigSpectralMathChanged = pyqtSignal()

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        loadUi(speclibUiPath('spectralmathwidget.ui'), self)

        self.mFunctionModel = SpectralMathFunctionModel()
        # self.mFunctionModel.addFunction(GenericSpectralMathFunction())
        self.mFunctionModel.sigChanged.connect(self.validate)
        self.mTableView: SpectralMathFunctionTableView
        self.mTableView.setModel(self.mFunctionModel)
        self.mTableView.selectionModel().selectionChanged.connect(self.onSelectionChanged)
        #self.mLastExpression = None
        #self.mDefaultExpressionToolTip = self.tbExpression.toolTip()
        #self.tbExpression.textChanged.connect(self.validate)
        self.mTestProfile = QgsFeature()
        self.mCurrentFunction: AbstractSpectralMathFunction = None

        m = QMenu()
        m.setToolTipsVisible(True)
        a = m.addAction('Add X Unit Conversion')
        a.triggered.connect(lambda *args: self.functionModel().addFunctions([XUnitConversion()]))

        a = m.addAction('Add Python Expression')
        a.triggered.connect(lambda *args : self.functionModel().addFunctions([GenericSpectralMathFunction()]))

        self.actionAddFunction.setMenu(m)
        self.actionRemoveFunction.triggered.connect(self.onRemoveFunctions)

        for tb in self.findChildren(QToolButton):
            tb: QToolButton
            a: QAction = tb.defaultAction()
            if isinstance(a, QAction) and isinstance(a.menu(), QMenu):
                tb.setPopupMode(QToolButton.MenuButtonPopup)


    def functionModel(self) -> SpectralMathFunctionModel:
        return self.mFunctionModel

    def onRemoveFunctions(self, *args):

        to_remove = set()
        for idx in self.mTableView.selectedIndexes():
            f = idx.data(Qt.UserRole)
            if isinstance(f, AbstractSpectralMathFunction):
                to_remove.add(f)

        if len(to_remove) > 0:
            self.functionModel().removeFunctions(list(to_remove))

    def onSelectionChanged(self, selected, deselected):

        self.actionRemoveFunction.setEnabled(selected.count() > 0)
        current: QModelIndex = self.mTableView.currentIndex()
        f = None
        if current.isValid():
            f = current.data(Qt.UserRole)

        if f != self.mCurrentFunction:
            wOld = self.scrollArea.takeWidget()
            self.mCurrentFunction = f

            if isinstance(f, AbstractSpectralMathFunction):
                w = self.mCurrentFunction.createWidget()
                self.scrollArea.setWidget(w)

    def tableView(self) -> SpectralMathFunctionTableView:
        return self.mTableView

    def setTextProfile(self, f: QgsFeature):
        self.mTestProfile = f
        self.validate()

    def spectralMathStack(self) -> typing.List[AbstractSpectralMathFunction]:
        stack = []
        if self.is_valid():
            stack.append(self.mTestFunction)
        return stack

    def validate(self) -> bool:
        test = SpectralMathResult(x=[1, 2], y=[1, 2], x_unit='nm', y_unit='')

        b = self.mFunctionModel.validate(test)

        return b
        expression: str = self.expression()
        self.mTestFunction.setExpression(expression)

        changed = expression != self.mLastExpression
        self.mLastExpression = expression
        result = self.mTestFunction.apply(test, self.mTestProfile)
        is_valid = AbstractSpectralMathFunction.is_valid_result(result)
        if is_valid:
            self.tbExpression.setToolTip(self.mDefaultExpressionToolTip)
            self.tbExpression.setStyleSheet('')
        else:
            self.tbExpression.setToolTip(str(self.mTestFunction.mError))
            self.tbExpression.setStyleSheet('color:red')

        if changed:
            self.sigSpectralMathChanged.emit()

        return is_valid

    def is_valid(self) -> bool:
        return self.validate()

    def expression(self) -> str:
        return self.tbExpression.toPlainText()