from PyQt4 import uic
from PyQt4.QtGui import QFileDialog, QMessageBox, QApplication
from PyQt4.QtCore import pyqtSignal, QFileSystemWatcher
from clt import ImageList, ImageListError

Ui_ImageBrowser, QWidget = uic.loadUiType("ui/ImageBrowser.ui")


class ImageBrowser(QWidget, Ui_ImageBrowser):
    """Widget to browse absorption and reference images"""

    windowTitleChanged = pyqtSignal(str)

    def __init__(self, settings, parent):
        super(ImageBrowser, self).__init__(parent=parent)
        self.settings = settings
        self.main_window = parent

        self.current_directory = './'
        self.path_to_dark_file = './tests/data/darks/default.tif'

        self.setupUi(self)
        self.loadSettings()

        self.image_list = ImageList()
        self.updateFileList(new_dir=True)

        self.watcher = QFileSystemWatcher(self)
        self.watcher.addPath(self.current_directory)
        self.watcher.directoryChanged.connect(self.handleWatcherDirectoryChanged)

    def updateFileList(self, new_dir=False):
        """Updates image_list to reflect files in current_directory.

        Pass new_dir=True if current_directory has changed.

        If an error occured, gives the user the option to select a different
        directory."""

        done = False
        while not done:
            try:
                if new_dir:
                    self.image_list.updateFileList(self.current_directory)
                else:
                    self.image_list.updateFileList()
            except ImageListError as err:
                info = (' Would you like to open a different directory?'
                        ' Press cancel to quit')
                pressed = QMessageBox.question(self, 'Error opening directory',
                                               str(err) + info,
                                               QMessageBox.No |
                                               QMessageBox.Yes |
                                               QMessageBox.Cancel)
                if pressed == QMessageBox.Yes:
                    self.setCurrentDirectory(self.openDirectoryDialog())
                    new_dir = True
                elif pressed == QMessageBox.No:
                    done = True
                elif pressed == QMessageBox.Cancel:
                    # user pressed cancel, quit!
                    done = True
                    self.main_window.close()
                    # TODO: find graceful way to quit
            else:
                # file updating was successful
                done = True

                if new_dir is False:
                    # This means we are just refreshing the current directory
                    # we probably want to keep the current index
                    previous_text = self.imageListCombo.currentText()

                # update image List combo
                self.imageListCombo.clear()
                self.imageListCombo.addItems(self.image_list.short_names)

                # update image index
                max_index = self.image_list.n_images - 1
                self.imageIndexSpin.setMaximum(max_index)
                labelString = 'of' + str(max_index)
                self.maxImageIndexLabel.setText(labelString)

                if new_dir is False:
                    # find if the previous image is still around
                    try:
                        ci = self.image_list.short_names.index(previous_text)
                    except ValueError:
                        # nope, it's not there. set current index to max index
                        ci = max_index
                else:
                    # if we have a new folder, then set the index to 0
                    ci = 0
                self.imageListCombo.setCurrentIndex(ci)
                self.imageIndexSpin.setValue(ci)

    def setCurrentDirectory(self, new_directory):
        """Sets the current directory.

        Never change self.current_directory directly. Use this function
        instead."""
        self.current_directory = new_directory
        self.windowTitleChanged.emit(self.current_directory)

    def loadSettings(self):
        self.settings.beginGroup('imagebrowser')
        self.setCurrentDirectory(str(self.settings.value('current_directory').toString()))
        self.path_to_dark_file = str(self.settings.value('path_to_dark_file').toString())
        self.settings.endGroup()

    def saveSettings(self):
        self.settings.beginGroup('imagebrowser')
        self.settings.setValue('current_directory', self.current_directory)
        self.settings.setValue('path_to_dark_file', self.path_to_dark_file)
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
            self.watcher.removePath(self.current_directory)
            self.setCurrentDirectory(new_directory)
            self.updateFileList(new_dir=True)
            self.watcher.addPath(self.current_directory)

    def handleDarkFileAction(self):
        """Called when the user clicks the Dark File menu option."""
        new_path_to_dark_file = str(QFileDialog.getOpenFileName(self,
                                    "Select dark file",
                                    self.path_to_dark_file))

        if new_path_to_dark_file != '':
            self.path_to_dark_file = new_path_to_dark_file

    def handleRefreshAction(self):
        self.updateFileList(new_dir=False)

    def handleCleanAction(self):
        print('handled')

    def handleUseCleanedAction(self, state):
        print('handled', state)

    def handleUseRoiWhileCleaningAction(self, state):
        print('handled', state)

    def odMinMaxStateChanged(self, new_state):
        print(new_state)

    def correctSaturationStateChanged(self, new_state):
        print(new_state)

    def handleWatcherDirectoryChanged(self, newDir):
        try:
            # see if updating the list would generate any errors
            ImageList(self.current_directory)
        except ImageListError:
            # if they do, then we probably are in the middle of a refresh
            # process, do nothing.
            return
        else:
            self.updateFileList(new_dir=False)
