from PyQt4 import uic
from PyQt4.QtGui import QFileDialog, QMessageBox, QProgressDialog
from PyQt4.QtCore import pyqtSignal, QFileSystemWatcher, Qt
import clt
import json
import numpy as np
import time
import os
import os.path as path

from widgets import SaveDialog

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
        self.is_cleaned = False
        self.use_roi_while_cleaning = False

        self.connectSignalsToSlots()

        self.image_list = clt.ImageList()
        self.updateFileList(new_dir=True)
        self.current_image_index = 0

        self.watcher = QFileSystemWatcher(self)
        self.watcher.addPath(self.current_directory)
        self.watcher.directoryChanged.connect(
            self.handleWatcherDirectoryChanged)
        self.updateCommentBox()

    def initialEmit(self):
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
        d['abs_image'] = clt.readImageFile(d['path_to_abs'])
        d['ref_image'] = clt.readImageFile(d['path_to_ref'])
        d['dark_image'] = clt.readImageFile(d['path_to_dark'])

        modified_time = time.ctime(os.path.getmtime(d['path_to_abs']))
        self.fileDateTime.setText(str(modified_time))

        if self.is_cleaned and self.useCleanedCheck.checkState() == 2:
            ref_image = self.clean_ref_images[index]
        else:
            ref_image = d['ref_image']
        d['div_image'] = clt.dividedImage(d['abs_image'], ref_image,
                                          d['dark_image'],
                                          od_minmax=self.getODMinMax(),
                                          correct_od_saturation=self.getODSaturationParms(),
                                          correct_saturation=self.getSaturationParms())
        d['image_type'] = self.getImageType()
        key = d['path_to_abs']
        if key not in self.global_save_info:
            self.global_save_info[key] = {}
        d['save_info'] = self.global_save_info[key]
        # d['save_info']['comment'] = str(self.commentTextEdit.toPlainText())

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
        print(self.current_image_index)
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
            if 'comment' not in self.global_save_info[key]:
                self.global_save_info[key]['comment'] = ''
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
            except clt.ImageListError as err:
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
                self.current_image_index = ci
                self.imageListCombo.setCurrentIndex(ci)
                self.imageIndexSpin.setValue(ci)


                # connect slot again once done adding
                self.imageListCombo.currentIndexChanged.connect(
                    self.handleImageListIndexChanged)
                self.imageIndexSpin.valueChanged.connect(
                    self.handleImageIndexValueChanged)

                self.is_cleaned = False
                self.useCleanedCheck.setCheckState(0)

                self.populateAndEmitImageInfo()
                self.purgeNonExistentEntries()

    def setCurrentDirectory(self, new_directory):
        """Sets the current directory.

        Never change self.current_directory directly. Use this function
        instead."""
        self.current_directory = new_directory
        self.windowTitleChanged.emit(self.current_directory)

    def loadSettings(self):
        self.settings.beginGroup('imagebrowser')
        self.setCurrentDirectory(
            str(self.settings.value('current_directory','./').toString()))
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
            except IOError as err:
                (errno, strerror) = err
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
        self.saveImageInfo()
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
        self.populateAndEmitImageInfo()

    def readAllRefImages(self, progress):
        progress.setLabelText('Reading Reference Images')
        self.ref_images = []
        for path_to_ref in self.image_list.reference_files:
            if progress.wasCanceled():
                return 1
            progress.setValue(progress.value() + 1)
            im = clt.normalize(clt.readImageFile(path_to_ref))
            self.ref_images.append(im)

    def generateBasis(self, progress):
        progress.setLabelText('Generating basis vectors')
        self.basis = []
        for b in clt.generateBasis(self.ref_images):
            progress.setValue(progress.value() + 1)
            if progress.wasCanceled():
                return 1
            self.basis.append(b)

    def readAllAbsImages(self, progress):
        progress.setLabelText('Reading absorption images')
        self.abs_images = []
        for path_to_abs in self.image_list.absorption_files:
            progress.setValue(progress.value() + 1)
            if progress.wasCanceled():
                return 1
            im = clt.readImageFile(path_to_abs)
            self.abs_images.append(im)

    def generateCleanRefs(self, progress):
        progress.setLabelText('Generating clean reference images')
        self.clean_ref_images = []

        abs_shape = self.abs_images[0].shape
        # TODO: insert code to get actual mask
        mask = self.getROIMask(abs_shape)
        self.is_cleaned = False
        for im in clt.generateCleanRefs(self.abs_images, self.basis, mask):
            progress.setValue(progress.value() + 1)
            if progress.wasCanceled():
                return 1
            self.clean_ref_images.append(im)
        else:
            self.is_cleaned = True

    def handleUseCleanedAction(self, state):
        if self.is_cleaned is False and state == 2:
            self.handleCleanAction()
        self.populateAndEmitImageInfo()

    def handleUseRoiWhileCleaningAction(self, state):
        self.use_roi_while_cleaning = bool(state)

    def handleImageTypeChanged(self, new_state_string):
        self.populateAndEmitImageInfo()

    def odMinMaxStateChanged(self, new_state):
        print(new_state)

    def correctSaturationStateChanged(self, new_state):
        print(new_state)

    def handleWatcherDirectoryChanged(self, newDir):
        try:
            # see if updating the list would generate any errors
            clt.ImageList(self.current_directory)
        except clt.ImageListError:
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

    def getSaturationParms(self):
        if self.correctSaturationCheckBox.checkState() == 0:
            return None
        else:
            gamma = 6.0666  # MHz
            return (self.satPixCountsSpin.value(), 2.0*self.detuningSpin.value()/gamma)

    def getODSaturationParms(self):
        if self.correctODSaturationCheckBox.checkState() == 0:
            return None
        else:
            return float(self.odSatSpin.value())


    def handleRoiChanged(self, new_roi):
        """Slot: Changes ROI used for cleaning images."""
        self.cleaning_roi = new_roi

    def getROIMask(self, abs_shape):
        mask = np.ones(abs_shape)
        if self.use_roi_while_cleaning:
            roi = self.cleaning_roi[0]  # 0th component is roi list
            mask[roi[0]:roi[2], roi[1]:roi[3]] = 0.0
        return mask

    def purgeNonExistentEntries(self):
        """Scan JSON database for files in current directory. If database has
        entries for which there are no files, then delete those entries."""
        for key in self.global_save_info.keys():
            if path.dirname(key) == self.current_directory:
                if not path.isfile(key):
                    # remove entry if this file does not exis
                    del self.global_save_info[key]
                    print('deleting: ' + key)


    def handleSaveAnalysis(self):
        save_dialog = SaveDialog(self.settings, self.global_save_info, self.image_list)
        save_dialog.exec_()