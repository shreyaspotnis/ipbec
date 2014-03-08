from PyQt4 import uic
from PyQt4.QtGui import QFileDialog, QMessageBox, QApplication
from clt import ImageList, ImageListError

Ui_ImageBrowser, QWidget = uic.loadUiType("ui/ImageBrowser.ui")


class ImageBrowser(QWidget, Ui_ImageBrowser):
    """Widget to browse absorption and reference images"""
    def __init__(self, settings, parent):
        super(ImageBrowser, self).__init__(parent=parent)
        self.settings = settings

        self.current_directory = './'

        self.setupUi(self)
        self.loadSettings()
        self.updateFileList()

    def updateFileList(self):
        """Updates image_list to reflect files in current_directory.

        If an error occured, gives the user the option to select a different
        directory."""
        done = False
        while not done:
            try:
                self.image_list = ImageList(self.current_directory)
            except ImageListError as err:
                info = (' Would you like to open a different directory?'
                        ' Press cancel to quit')
                pressed = QMessageBox.question(self, 'Error opening directory',
                                               str(err) + info,
                                               QMessageBox.No |
                                               QMessageBox.Yes |
                                               QMessageBox.Cancel)
                if pressed == QMessageBox.Yes:
                    self.current_directory = self.openDirectoryDialog()
                elif pressed == QMessageBox.No:
                    done = True
                elif pressed == QMessageBox.Cancel:
                    # user pressed cancel, quit!
                    done = True
                    # TODO: find graceful way to quit
            else:
                done = True
                print(self.image_list.absorption_files)

    def loadSettings(self):
        self.settings.beginGroup('imagebrowser')
        self.current_directory = str(self.settings.value('current_directory').toString())
        self.settings.endGroup()

    def saveSettings(self):
        self.settings.beginGroup('imagebrowser')
        self.settings.setValue('current_directory', self.current_directory)
        self.settings.endGroup()

    def openDirectoryDialog(self):
        """Opens a dialog to select and new directory and returns path to
        selected directory."""
        return str(QFileDialog.getExistingDirectory(self, "Open Directory",
                   self.current_directory, QFileDialog.ShowDirsOnly))

    def handleOpenDirectoryAction(self):
        """Called when the user clicks the Open Directory button."""

        new_directory = self.openDirectoryDialog()

        if new_directory is not '' and new_directory != self.current_directory:
            self.current_directory = new_directory
            self.updateFileList()
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

