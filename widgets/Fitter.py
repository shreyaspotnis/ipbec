from PyQt4 import uic
from clt import fittools
from clt import imtools
from PyQt4.QtGui import QDoubleSpinBox, QLabel
from PyQt4.QtCore import pyqtSignal
import numpy as np


Ui_Fitter, QWidget = uic.loadUiType("ui/Fitter.ui")


class Fitter(QWidget, Ui_Fitter):
    """Widget to fit functions to images."""

    # connect to imageView
    imageChanged = pyqtSignal(object)

    # connect to ROIH and ROIV viewer
    horDataChanged = pyqtSignal(object, object, object)
    verDataChanged = pyqtSignal(object, object, object)

    # connect to analyzer
    doneFitting = pyqtSignal()

    def __init__(self, settings, parent):
        super(Fitter, self).__init__(parent=parent)
        self.settings = settings
        self.main_window = parent

        self.initialized = False
        self.is_fitted = False
        self.has_roi_h = False
        self.has_roi_v = False
        self.has_roi_int = False

        self.setupUi(self)

    def populateFitTypes(self):
        """Populate Fit Type selector with available fitting functions.

        Called once during initialization. Not needed anytime else"""
        self.fitNames = [f.name for f in fittools.fittypes]
        self.fitTypeCombo.addItems(self.fitNames)

    def loadSettings(self):
        pass

    def initialize(self):
        """Called when the first image is emitted. This makes sure that there
        is a valid image to work with and initializes guess boxes"""
        self.loadSettings()
        self.createFitter(0)
        self.populateFitTypes()
        self.populateGuessBoxes()
        self.updateGuessBoxes()

    def handleImageChanged(self, new_image_info):
        """Slot: Called when image browser changes image.

        Extracts relevant image. If Auto guess, Auto Fit or Auto Transfer are
        enabled, handles guessing, transfer or fitting. Finally emits the image
        for image_view to update.
        """
        self.is_fitted = False
        self.image_info = new_image_info
        im_type = self.image_info['image_type']
        self.current_image = self.image_info[im_type]
        if not self.initialized:
            self.initialize()
            self.initialized = True
        self.fitter.updateImage(self.current_image, keepGuess=True)

        aG = self.autoGuessCheck.isChecked()
        aF = self.autoFitCheck.isChecked()
        aT = self.autoTransferCheck.isChecked()

        if aG and not aT:
            self.handleAutoGuess()
        elif aT:
            newValues = [fv for fv in self.fitter.fitParameters]
            self.fitter.setGuess(newValues)
            self.updateGuessBoxes()

        if aF:
            self.handleAutoFit()

        self.handleEmitImage()

    def handleGuessClicked(self):
        """Called when user presses the Guess button.

        Guesses initial values for fitting and updates Guess boxes.
        """
        self.handleAutoGuess()
        self.handleEmitImage()

    def handleAutoGuess(self):
        self.fitter.autoGuess()
        self.updateGuessBoxes()

    def handleFitClicked(self):
        self.handleAutoFit()
        self.handleEmitImage()

    def handleAutoFit(self):
        nCalls = int(self.nIterationsBox.value())
        if self.useROICheck.isChecked():
            self.fit_output = self.fitter.fit(nCalls, self.fitROI)
        else:
            self.fit_output = self.fitter.fit(nCalls)
        self.fitted_data = self.fitter.fittedData()

        # TODO: update dictionary with all the fitting parameters
        self.parseFitOutput(self.fit_output)
        self.updateFitBoxes()

        self.is_fitted = True
        self.doneFitting.emit()

    def updateFitBoxes(self):
        """Updates fit spinboxes when fitter fits to data."""
        for p, sd, l in zip(self.fitter.fitParameters,
                            self.fitter.fitParmSD,
                            self.fitBox):
            l.setText('{0:.2f}+-{1:.2f}'.format(p, sd))

    def handleFitToGuessClicked(self):
        new_values = [fv for fv in self.fitter.fitParameters]
        self.fitter.setGuess(new_values)
        self.updateGuessBoxes()
        self.handleEmitImage()

    def handleContinueClicked(self):
        new_values = [fv for fv in self.fitter.fitParameters]
        self.fitter.setGuess(new_values)
        self.handleAutoFit()

    def handleFitTypeChanged(self, new_index):
        if not self.initialized:
            return
        self.depopulateGuessBoxes()
        self.createFitter(new_index)
        self.populateGuessBoxes()

    def handleImageTypeChanged(self, new_index):
        self.handleEmitImage()

    def handleGuessValueChanged(self, new_value):
        new_values = [float(sp.value()) for sp in self.guessBox]
        self.fitter.setGuess(new_values)
        self.handleEmitImage()

    def createFitter(self, newIndex):
        im_type = self.image_info['image_type']
        self.current_image = self.image_info[im_type]
        self.fitter = fittools.fittypes[newIndex](self.current_image)

    def populateGuessBoxes(self):
        self.guessBox = []
        self.fitBox = []
        sI = 1  # TODO: do something smart about this
        for i, n in enumerate(self.fitter.parameterNames):
            spGuess = QDoubleSpinBox(self)
            spGuess.setRange(-1e10, 1e10)
            spGuess.setKeyboardTracking(False)
            spFit = QLabel('0.0')
            self.parmGrid.addWidget(QLabel(n, parent=self), i+sI+1, 0)
            self.parmGrid.addWidget(spGuess, i+sI+1, 1)
            self.parmGrid.addWidget(spFit, i+sI+1, 2)

            self.guessBox.append(spGuess)
            self.fitBox.append(spFit)

        self.connectGuessBoxes()

    def depopulateGuessBoxes(self):
        self.disconnectGuessBoxes()
        sI = 1
        for i, n in enumerate(self.fitter.parameterNames):
            for j in range(3):
                w = self.parmGrid.itemAtPosition(i+sI+1, j)
                if w != 0:
                    w.widget().deleteLater()
        self.guessBox = []
        self.fitBox = []

    def connectGuessBoxes(self):
        for gb in self.guessBox:
            gb.valueChanged.connect(self.handleGuessValueChanged)

    def disconnectGuessBoxes(self):
        for gb in self.guessBox:
            gb.valueChanged.disconnect(self.handleGuessValueChanged)

    def updateGuessBoxes(self):
        """Updates guess spinboxes when fitter guesses."""
        self.disconnectGuessBoxes()
        for g, sp in zip(self.fitter.guess, self.guessBox):
            sp.setValue(g)
        self.connectGuessBoxes()

    def handleEmitImage(self):
        index = self.imageTypeCombo.currentIndex()
        if index == 0:
            emit_image = self.current_image
        elif index == 1:
            emit_image = self.fitter.fittedData()
        elif index == 2:
            emit_image = self.fitter.guessData()
        elif index == 3:
            # data - fit
            emit_image = self.fitter.fittedData() - self.current_image
        elif index == 4:
            emit_image = self.fitter.guessData() - self.current_image

        self.emit_image = emit_image
        self.imageChanged.emit(emit_image)
        self.emitROIHdata()
        self.emitROIVdata()

    def parseFitOutput(self, fit_output):
        (p, cov_p, info_dict, mesg, ier, s_sq, time_diff) = fit_output
        self.fit_details_string = (("Time Taken:\t{0:.2f}\n"
                                 "Function Calls:\t{1:d}\n"
                                 "Reduced chi squared:\t{2:.3f}\n"
                                 "Message:\t{3:s}")
                                 .format(time_diff, info_dict['nfev'], s_sq,
                                         mesg))
        self.fitDetailsLabel.setText(self.fit_details_string)

    def handleROIHChanged(self, new_roi):
        self.has_roi_h = True
        self.roi_h = new_roi
        if self.initialized:
            self.emitROIHdata()

    def handleROIVChanged(self, new_roi):
        self.has_roi_v = True
        self.roi_v = new_roi
        if self.initialized:
            self.emitROIVdata()

    def handleROIIntChanged(self, new_roi):
        self.has_roi_int = True
        self.roi_int = new_roi

    def emitROIHdata(self):
        if self.has_roi_h:
            if self.imageTypeCombo.currentIndex() is 0 and self.is_fitted:
                indices, fit = imtools.getROISlice(self.fitted_data, self.roi_h)
            else:
                fit = None
            indices, data = imtools.getROISlice(self.emit_image, self.roi_h)
            self.horDataChanged.emit(indices, data, fit)

    def emitROIVdata(self):
        if self.has_roi_v:
            if self.imageTypeCombo.currentIndex() is 0 and self.is_fitted:
                indices, fit = imtools.getROISlice(self.fitted_data, self.roi_v)
            else:
                fit = None
            indices, data = imtools.getROISlice(self.emit_image, self.roi_v)
            self.verDataChanged.emit(indices, data, fit)
