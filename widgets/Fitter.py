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

    def handleImageChanged(self, new_dict):
        pass
