from PyQt4 import uic
from PyQt4.QtGui import QMessageBox, QCheckBox, QFileDialog
from clt import fittools
from widgets import Analyzer
import string
import numpy as np
import os.path as path

Ui_SaveDialog, QDialog = uic.loadUiType("ui/SaveDialog.ui")


class SaveDialog(QDialog, Ui_SaveDialog):
    """Handles saving analyzed data."""

    def __init__(self, settings, global_info, curr_image_list):
        super(SaveDialog, self).__init__()
        self.settings = settings
        self.global_info = global_info
        self.curr_image_list = curr_image_list
        self.analyzed_outputs = Analyzer.Outputs
        self.setupUi(self)
        self.added_check_boxes = False
        self.save_folder = './'
        self.loadSettings()

        self.fitNames = [f.name for f in fittools.fittypes]
        self.fitTypeCombo.addItems(self.fitNames)

    def handleFitTypeChanged(self, new_type):
        if self.added_check_boxes:
            # add code to remove checkboxes
            for i, n in enumerate(self.all_labels):
                w = self.cbgrid.itemAtPosition(i, 0)
                if w != 0:
                    w.widget().deleteLater()
            self.save_check_boxes = []

        self.fit_type = str(new_type)
        fitter = fittools.fit_types_dict[self.fit_type]

        self.fit_parms = fitter.parameterNames

        self.all_labels = self.fit_parms + self.analyzed_outputs
        self.save_check_boxes = [QCheckBox(fL, self) for fL in self.all_labels]
        for i, s in enumerate(self.save_check_boxes):
            self.cbgrid.addWidget(s, i, 0)

        self.added_check_boxes = True
        self.findErrors()

    def handleSelectAll(self):
        for cb in self.save_check_boxes:
            cb.setCheckState(2)

    def handleSelectNone(self):
        for cb in self.save_check_boxes:
            cb.setCheckState(0)

    def handleSave(self):
        if self.findErrors():
            return
        data = []
        for k in self.curr_image_list.absorption_files:
            data_row = []
            image_info = self.global_info[k]
            for i, label in enumerate(self.all_labels):
                if self.save_check_boxes[i].checkState() == 2:
                    # we want this to be saved
                    if i < len(self.fit_parms):
                        value = image_info['fitter'][self.fit_type]['parms'][label]
                    else:
                        value = image_info['analyzer'][self.fit_type]['output'][label]
                    data_row.append(value)
            data.append(data_row)

        data_np = np.array(data)
        sh = data_np.shape
        data_full = np.zeros((sh[0], sh[1] + 1))
        data_full[:, 0] = np.arange(sh[0])
        data_full[:, 1:] = data_np

        header = ['#index']
        for i, label in enumerate(self.all_labels):
                if self.save_check_boxes[i].checkState() == 2:
                    # we want this to be saved
                    header.append(label)
        header_string = string.join(header, '\t')

        print(self.save_folder)
        file_name = str(QFileDialog.getSaveFileName(self, caption='Save as...',
                                                directory=self.save_folder))
        if file_name != '':
            np.savetxt(file_name, data_full, delimiter='\t',
                       header=header_string)
            self.save_folder = path.dirname(file_name)
            self.saveSettings()

    def findErrors(self):
        errors = False
        not_analyzed = [k for k in self.curr_image_list.absorption_files
                        if k not in self.global_info]
        analyzed = [k for k in self.curr_image_list.absorption_files
                    if k in self.global_info]
        if len(not_analyzed) > 0:
            errors = True

        msg = 'ERRORS:\nNo info for the following files:'
        no_info_string = string.join([msg] + not_analyzed, '\n')

        no_fit_info = []
        for k in analyzed:
            image_info = self.global_info[k]
            if 'fitter' not in image_info:
                no_fit_info.append(k)
            elif self.fit_type not in image_info['fitter']:
                no_fit_info.append(k)
        if len(no_fit_info) > 0:
            errors = True
        no_analyzer_info = []
        for k in analyzed:
            image_info = self.global_info[k]
            if 'analyzer' not in image_info:
                no_analyzer_info.append(k)
            elif self.fit_type not in image_info['analyzer']:
                no_analyzer_info.append(k)
        if len(no_analyzer_info) > 0:
            errors = True

        msg_fit = 'No fit info for the following files:'
        msg_an = 'No Analysis info for the following files:'
        no_fit_string = string.join([msg_fit] + no_fit_info, '\n')
        no_an_string = string.join([msg_an] + no_analyzer_info, '\n')

        final_string = string.join([no_info_string, no_fit_string, no_an_string], '\n\n')
        self.errorLabel.setText(final_string)
        return errors

    def loadSettings(self):
        self.settings.beginGroup('savedialog')
        self.save_folder = str(self.settings.value('save_folder', './').toString())
        self.settings.endGroup()

    def saveSettings(self):
        self.settings.beginGroup('savedialog')
        self.settings.setValue('save_folder', self.save_folder)
        self.settings.endGroup()