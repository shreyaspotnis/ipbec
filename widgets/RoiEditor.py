from PyQt4 import uic
from PyQt4.QtCore import pyqtSignal
import pyqtgraph as pg

Ui_RoiEditor, QWidget = uic.loadUiType("ui/RoiEditor.ui")


class RoiEditor(QWidget, Ui_RoiEditor):
    """Interface to edit a ROI by precisely punching numbers."""

    roiChanged = pyqtSignal(tuple)

    def __init__(self, settings, imageView, parent=None,
                 name='ROI', pen=(1, 9), axis=0):
        QWidget.__init__(self, parent)

        self.name = name
        self.imv = imageView
        self.pen = pen
        self.axis = axis

        self.settings = settings

        self.setupUi(self)

        self.hvCombo.setCurrentIndex(axis)
        self.pSB = [self.p1xSB, self.p1ySB, self.p2xSB, self.p2ySB]
        self.wSB = [self.wxSB, self.wySB]

        self.roiNameLabel.setText(name)

        iv = self.loadValues()

        self.updatePState(iv)
        self.updateWState(iv)

        self.roi = pg.ROI([iv[0], iv[1]], [iv[2]-iv[0], iv[3]-iv[1]], pen=pen)
        self.imv.addItem(self.roi)
        self.roi.addScaleHandle([1, 1], [0, 0])
        self.roi.addScaleHandle([0, 0], [1, 1])

        self.connectButtons()
        self.connectPSpinBoxes()
        self.connectWSpinBoxes()
        self.connectROI()

    def loadValues(self):
        self.settings.beginGroup('RoiEditor'+self.name)
        roi_string = str(self.settings.value('roi').toString())
        if roi_string is not "":
            initValues = eval(roi_string)
        else:
            initValues = [0, 0, 100, 100]
        self.settings.endGroup()
        print(initValues)
        return initValues

    def saveSettings(self):
        val = [sb.value() for sb in self.pSB]
        self.settings.beginGroup('RoiEditor'+self.name)
        self.settings.setValue('roi', repr(val))
        self.settings.endGroup()

    def connectButtons(self):
        self.stretchButton.clicked.connect(self.handleStretch)
        self.pxButton.clicked.connect(self.handle1px)
        self.copyButton.clicked.connect(self.handleCopy)
        self.pasteButton.clicked.connect(self.handlePaste)

    def connectPSpinBoxes(self):
        for sb in self.pSB:
            sb.valueChanged.connect(self.handlePSB)

    def disconnectPSpinBoxes(self):
        for sb in self.pSB:
            sb.valueChanged.disconnect(self.handlePSB)

    def connectWSpinBoxes(self):
        for sb in self.wSB:
            sb.valueChanged.connect(self.handleWSB)

    def disconnectWSpinBoxes(self):
        for sb in self.wSB:
            sb.valueChanged.disconnect(self.handleWSB)

    def connectROI(self):
        self.roi.sigRegionChanged.connect(self.handleUpdateROI)

    def disconnectROI(self):
        self.roi.sigRegionChanged.disconnect(self.handleUpdateROI)

    def handlePSB(self, newValues):
        """Called when any of the values in P1 and P2 are changed."""
        nV = [sb.value() for sb in self.pSB]

        self.updateAll(nV)

    def handleWSB(self, newValues):
        """Called when any of the values in W are changed."""
        V = [sb.value() for sb in self.pSB]
        V[2] = V[0] + self.wSB[0].value()
        V[3] = V[1] + self.wSB[1].value()

        self.updateAll(V)

    def updateROIState(self, v):
        """Updates the ROI that is drawn on the image."""
        st = {}
        st['angle'] = 0
        st['pos'] = pg.Point(v[0], v[1])
        st['size'] = pg.Point(v[2] - v[0], v[3] - v[1])
        self.roi.setState(st)

    def updatePState(self, V):
        for sb, v in zip(self.pSB, V):
            sb.setValue(v)

    def updateWState(self, V):
        self.wSB[0].setValue(V[2] - V[0])
        self.wSB[1].setValue(V[3] - V[1])

    def updateAll(self, V):
        self.disconnectROI()
        self.disconnectPSpinBoxes()
        self.disconnectWSpinBoxes()

        self.updatePState(V)
        self.updateWState(V)
        self.updateROIState(V)

        self.connectROI()
        self.connectPSpinBoxes()
        self.connectWSpinBoxes()

        self.roiChanged.emit((V, self.hvCombo.currentIndex()))

    def handleStretch(self):
        """Stretch the ROI in a direction perpendicular to the
        integration direction."""
        shape = self.imv.getImageItem().image.shape
        V = [sb.value() for sb in self.pSB]
        if self.hvCombo.currentIndex() is 0:
            V[1] = 0
            V[3] = shape[1]
        else:
            V[0] = 0
            V[2] = shape[1]

        self.updateAll(V)

    def handle1px(self):
        """Make the ROI 1 pixel wide."""
        V = [sb.value() for sb in self.pSB]
        if self.hvCombo.currentIndex():
            cen = float(V[1] + V[3])/2
            V[1] = int(cen)
            V[3] = int(cen + 1)
        else:
            cen = float(V[0] + V[2])/2
            V[0] = int(cen)
            V[2] = int(cen + 1)

        self.updateAll(V)

    def centerROI(self, newCenter):
        V = [sb.value() for sb in self.pSB]
        if self.hvCombo.currentIndex() is 1:
            w = V[3] - V[1]
            p1 = newCenter[1] - w/2
            p2 = p1 + w
            newValues = [V[0], p1, V[2], p2]
        else:
            w = V[2] - V[0]
            p1 = newCenter[0] - w/2
            p2 = p1 + w
            newValues = [p1, V[1], p2, V[3]]

        self.updateAll(newValues)

    def handleCopy(self):
        print('couyp')

    def handlePaste(self):
        print('past')

    def handleUpdateROI(self, roi):
        st = roi.getState()
        pos = st['pos']
        size = st['size']
        V = [pos[0], pos[1], pos[0] + size[0], pos[1] + size[1]]

        self.updateAll(V)
