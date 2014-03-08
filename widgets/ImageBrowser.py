from PyQt4 import QtGui, uic

Ui_ImageBrowser, QWidget = uic.loadUiType("ui/ImageBrowser.ui")


class ImageBrowser(QWidget, Ui_ImageBrowser):
    """Widget to browse absorption and reference images"""
    def __init__(self, settings, parent):
        super(ImageBrowser, self).__init__(parent=parent)
        self.settings = settings
        self.setupUi(self)

    def handleOpenDirectoryAction(self):
        print('handled')

    def handleDarkFileAction(self):
        print('handled')

    def handleRefreshAction(self):
        print('handled')

    def handleCleanAction(self):
        print('handled')

    def handleUseCleanedAction(self, state):
        print('handled', state)

    def handleUseRoiWhileCleaningAction(self, state):
        print('handled', state)

