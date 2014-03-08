from PyQt4 import uic
from PyQt4.QtGui import QFileDialog

Ui_ImageBrowser, QWidget = uic.loadUiType("ui/ImageBrowser.ui")


class ImageBrowser(QWidget, Ui_ImageBrowser):
    """Widget to browse absorption and reference images"""
    def __init__(self, settings, parent):
        super(ImageBrowser, self).__init__(parent=parent)
        self.settings = settings

        self.current_directory = './'

        self.setupUi(self)
        self.loadSettings()

    def loadSettings(self):
        self.settings.beginGroup('imagebrowser')
        self.current_directory = str(self.settings.value('current_directory').toString())
        self.settings.endGroup()

    def saveSettings(self):
        self.settings.beginGroup('imagebrowser')
        self.settings.setValue('current_directory', self.current_directory)
        self.settings.endGroup()

    def handleOpenDirectoryAction(self):
        """Called when the user clicks the Open Directory button."""
        new_directory = str(QFileDialog.getExistingDirectory(self,
                           "Open Directory",
                           self.current_directory,
                           QFileDialog.ShowDirsOnly))
        print(new_directory)
        self.current_directory = new_directory

        # if newDirectory != '' and newDirectory != self.currentDirectory:
        #     self.watcher.removePath(self.currentDirectory)
        #     self.currentDirectory = newDirectory
        #     self.internalConfig.set('ScanDirectory', 'currentDirectory',
        #                             self.currentDirectory)
        #     self.updateInternalConfig()
        #     self.updateOpenDirectoryToolTip()
        #     self.handleRefresh(changeDir=True)

        #     self.watcher.addPath(self.currentDirectory)

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

