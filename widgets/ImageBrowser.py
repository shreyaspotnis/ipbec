from PyQt4 import uic
from PyQt4.QtGui import QFileDialog, QMessageBox, QApplication, QProgressDialog
from PyQt4.QtCore import pyqtSignal, QFileSystemWatcher, Qt
from clt import ImageList, ImageListError, readImageFile, dividedImage
import json

import pprint

Ui_ImageBrowser, QWidget = uic.loadUiType("ui/ImageBrowser.ui")


class ImageBrowser(QWidget, Ui_ImageBrowser):
    """Widget to browse absorption and reference images"""

    windowTitleChanged = pyqtSignal(str)
    imageChanged = pyqtSignal(dict)

    def __init__(self, settings, parent):
        super(ImageBrowser, self).__init__(parent=parent)
        self.settings = settings
        self.main_window = parent

        self.current_directory = './'
        self.path_to_dark_file = './tests/data/darks/default.tif'
        self.path_to_json_db = 'image_save_info.json'

        self.current_image_info = {}

        self.setupUi(self)
        self.loadSettings()
        self.use_cleaned_refs = False
        self.is_cleaned = False
        self.use_roi_while_cleaning = False

        self.connectSignalsToSlots()

        self.image_list = ImageList()
        self.updateFileList(new_dir=True)
        self.current_image_index = 0

        self.watcher = QFileSystemWatcher(self)
        self.watcher.addPath(self.current_directory)
        self.watcher.directoryChanged.connect(
            self.handleWatcherDirectoryChanged)
        self.updateCommentBox()
        self.populateAndEmitImageInfo()

    def populateAndEmitImageInfo(self):
        """Populates current_image_info with all the required information about
        the current image. It then emits the imageChanged signal"""
        d = self.current_image_info
        index = self.imageListCombo.currentIndex()
        d['index'] = index
        d['path_to_abs'] = self.image_list.absorption_files[index]
        d['path_to_ref'] = self.image_list.reference_files[index]
        d['path_to_dark'] = self.path_to_dark_file
        d['abs_image'] = readImageFile(d['path_to_abs'])
        d['ref_image'] = readImageFile(d['path_to_ref'])
        d['dark_image'] = readImageFile(d['path_to_dark'])
        d['div_image'] = dividedImage(d['abs_image'], d['ref_image'],
                                      d['dark_image'],
                                      od_minmax=self.getODMinMax())
        d['image_type'] = self.getImageType()
        d['save_info'] = {}
        d['save_info']['comment'] = str(self.commentTextEdit.toPlainText())

        # pprint.pprint(d)

        self.imageChanged.emit(d)

    def getImageType(self):
        imtype = str(self.imageTypeCombo.currentText())
        imcode = {'Absorption': 'abs_image', 'Reference': 'ref_image',
                  'Divided': 'div_image', 'Dark': 'dark_image'}
        return imcode[imtype]

    def handleImageIndexValueChanged(self, new_index):
        """Slot: called when the user changes the current index."""
        # just update imageList. handleImageListIndexChanged will take care of
        # the rest
        self.imageListCombo.setCurrentIndex(new_index)

    def handleImageListIndexChanged(self, new_index):
        """Slot: called when the user changes the current image in the combo
        box."""
        # we need to update imageIndexSpin, but also want to avoid recursive
        # updates. Hence we disconnect slots before updating.

        self.saveImageInfo()

        self.imageIndexSpin.valueChanged.disconnect(
            self.handleImageIndexValueChanged)
        self.imageIndexSpin.setValue(new_index)
        self.imageIndexSpin.valueChanged.connect(
            self.handleImageIndexValueChanged)

        self.current_image_index = new_index
        self.updateCommentBox()
        self.populateAndEmitImageInfo()

    def saveImageInfo(self):
        """Get save_info contents of current_image_info and save it in
        global_save_info.

        TODO: write better description of this function.
        """
        comment = str(self.commentTextEdit.toPlainText())
        key = self.image_list.absorption_files[self.current_image_index]
        # if key not in self.global_save_info:
        #     self.global_save_info[key] = {}
        self.global_save_info[key] = self.current_image_info['save_info']
        self.global_save_info[key]['comment'] = comment

    def updateCommentBox(self):
        """Updates comment box to display comment for the current image."""
        key = self.image_list.absorption_files[self.current_image_index]
        if key not in self.global_save_info:
            self.commentTextEdit.setPlainText('')
        else:
            comment = self.global_save_info[key]['comment']
            self.commentTextEdit.setPlainText(comment)

    def connectSignalsToSlots(self):
        self.imageIndexSpin.valueChanged.connect(
            self.handleImageIndexValueChanged)
        self.imageListCombo.currentIndexChanged.connect(
            self.handleImageListIndexChanged)

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

                # disconnect slots before adding items
                self.imageListCombo.currentIndexChanged.disconnect(
                    self.handleImageListIndexChanged)
                self.imageIndexSpin.valueChanged.disconnect(
                    self.handleImageIndexValueChanged)

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

                # connect slot again once done adding
                self.imageListCombo.currentIndexChanged.connect(
                    self.handleImageListIndexChanged)
                self.imageIndexSpin.valueChanged.connect(
                    self.handleImageIndexValueChanged)

                self.populateAndEmitImageInfo()

    def setCurrentDirectory(self, new_directory):
        """Sets the current directory.

        Never change self.current_directory directly. Use this function
        instead."""
        self.current_directory = new_directory
        self.windowTitleChanged.emit(self.current_directory)

    def loadSettings(self):
        self.settings.beginGroup('imagebrowser')
        self.setCurrentDirectory(
            str(self.settings.value('current_directory').toString()))
        self.path_to_dark_file = str(
            self.settings.value('path_to_dark_file',
            self.path_to_dark_file).toString())
        self.path_to_json_db = str(self.settings.value(
                                   'path_to_json_db',
                                   './image_save_info.json').toString())

        self.settings.endGroup()
        self.loadJsonFile()

    def loadJsonFile(self):
        info = ('\n\nSomething bad has happened and I am not equipped to '
                'handle it. Please check if ' + self.path_to_json_db +
                ' exists. If it does, then make a backup of this file as '
                'it has a lot of information. Press yes if you would like '
                'to select a new database file. This has to be a valid JSON '
                'file. {} is an empty but valid JSON file. '
                'Press no if you want to '
                'create a new empty database at the same location. '
                'Press cancel if you want me be to crash horribly but '
                'without touching the database file.')
        done = False
        while not done:
            try:
                with open(self.path_to_json_db, 'r') as f:
                    self.global_save_info = json.loads(f.read())
            except IOError as (errno, strerror):
                # something bad wrong
                msg = str(strerror)
            except ValueError as err:
                msg = str(err)
            except:
                msg = "Unknown error."
            else:
                done = True

            if not done:
                pressed = QMessageBox.critical(self, 'Error opening database',
                                               msg + info, QMessageBox.No |
                                               QMessageBox.Yes |
                                               QMessageBox.Cancel)
                if pressed == QMessageBox.Yes:
                    # file dialog
                    new_path = str(QFileDialog.getOpenFileName(self,
                                   "Select new JSON file",
                                   self.path_to_json_db))
                    self.path_to_json_db = new_path
                    done = False
                elif pressed == QMessageBox.No:
                    self.global_save_info = {}
                    done = True
                elif pressed == QMessageBox.Cancel:
                    done = True
                    self.global_save_info = {}
                    self.path_to_json_db = './temp_crash_json'
                    self.main_window.close()

    def saveSettings(self):
        self.settings.beginGroup('imagebrowser')
        self.settings.setValue('current_directory', self.current_directory)
        self.settings.setValue('path_to_dark_file', self.path_to_dark_file)
        self.settings.setValue('path_to_json_db', self.path_to_json_db)
        self.settings.endGroup()
        json_file_as_string = json.dumps(self.global_save_info, indent=4,
                                         separators=(',', ': '))
        with open(self.path_to_json_db, 'w') as f:
            f.write(json_file_as_string)

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
        progress = QProgressDialog('Reading Reference images', 'Abort',
                                   0, 4.0*self.image_list.n_images, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(1)

        if self.readAllRefImages(progress):
            return
        if self.generateBasis(progress):
            return
        if self.readAllAbsImages(progress):
            return
        if self.generateCleanRefs(progress):
            return

        progress.setValue(4.0*self.image_list.n_images)

    def readAllRefImages(self, progress):
        pass

    def generateBasis(self, progress):
        pass

    def readAllAbsImages(self, progress):
        pass

    def generateCleanRefs(self, progress):
        pass

    def handleUseCleanedAction(self, state):
        self.use_cleaned_refs = bool(state)
        self.populateAndEmitImageInfo()

    def handleUseRoiWhileCleaningAction(self, state):
        self.use_roi_while_cleaning = bool(state)

    def handleImageTypeChanged(self, new_state_string):
        print('new_state_string')

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

    def getODMinMax(self):
        """Return a tuple with min and max OD values read from the UI.
        returns None if odMinMax check button is not checked."""
        if self.odMinMaxCheck.checkState() == 0:
            return None
        else:
            return (self.odMinSpin.value(), self.odMaxSpin.value())
