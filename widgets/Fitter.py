from PyQt4 import uic
from clt import fittools


Ui_Fitter, QWidget = uic.loadUiType("ui/Fitter.ui")


class Fitter(QWidget, Ui_Fitter):
    """Widget to fit functions to images."""

    def __init__(self, settings, parent):
        super(Fitter, self).__init__(parent=parent)
        self.settings = settings
        self.main_window = parent

        self.setupUi(self)
        self.loadSettings()
        self.populateFitTypes()

    def populateFitTypes(self):
        self.fitNames = [f.name for f in fittools.fittypes]
        self.fitTypeCombo.addItems(self.fitNames)

    def loadSettings(self):
        pass

    def handleImageChanged(self, new_image_info):
        self.image_info = new_image_info

    def handleGuessClicked(self):
        print('guess')

    def handleFitClicked(self):
        print('fit')

    def handleFitToGuessClicked(self):
        print('fittoguess')

    def handleContinueClicked(self):
        print('continue')
