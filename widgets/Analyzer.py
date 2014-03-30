from PyQt4.QtGui import QWidget
import numpy as np


class Analyzer(QWidget):
    """Widget to analyze fit data. Extract relevant parameters."""

    Inputs = ['TOF(ms)', 'Pixel Size(um)', 'Detuning(MHz)',
              'Exposure Time (us)', 'Probe Intensity/I0', 'fx(Hz)', 'fy(Hz)',
              'fz(Hz)']
    Outputs = ['Fitted Atom Number', 'Integrated Atom Number', 'H Temp(uK)',
               'V Temp(uK)', 'Peak Density(cm^-3)', 'Collision Rate',
               'BEC Fraction', 'Chemical potential(nK)']
    OutputFormats = ['%.2e', '%.2e', '%.2g', '%.2g', '%g', '%g', '%.3g',
                     '%.1g']

    def __init__(self, settings, parent=None):
        super(Analyzer, self).__init__(parent)
        self.parent = parent
        self.settings = settings
        self.initialized = False

    def initUI(self):
        pass

    def handleImageChanged(self, new_image_info):
        self.image_info = new_image_info
        if not self.initialized:
            self.initUI()
            self.initialized = True

    def handleDoneFitting(self, fit_type):
        print('done fitting', fit_type)
