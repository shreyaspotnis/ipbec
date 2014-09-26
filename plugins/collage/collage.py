from PyQt4 import uic
from PyQt4 import QtGui, QtCore
import pyqtgraph as pg
import os
from clt.imtools import getROISlice, getSubImage
from widgets import ImageView
import numpy as np



class PluginDialog(QtGui.QDialog):

    """Handles the plugin dialogbox."""

    name = "Collage"

    def __init__(self, settings, data_dict):
        super(PluginDialog, self).__init__()
        self.settings = settings
        self.data_dict = data_dict
        self.div_images = self.data_dict['div_images']
        self.n_images = len(self.div_images)

        self.roi_h = self.data_dict['roi_h']
        self.roi_v = self.data_dict['roi_v']
        self.roi_int = self.data_dict['roi_int']

        self.rois = [self.roi_h, self.roi_v, self.roi_int]
        self.spinbox_values = [0, 1, len(self.div_images)]

        self.settings.beginGroup('savedialog')
        self.save_folder = str(self.settings.value('save_folder', './').toString())
        self.settings.endGroup()

        self.grid = QtGui.QGridLayout(self)
        self.setLayout(self.grid)

        self.image_view = ImageView(self.settings, self)
        self.grid.addWidget(self.image_view, 0, 0, 3, 3)

        self.labels = [QtGui.QLabel(a) for a in ["Start", "Step", "End"]]
        self.spin_boxes = [QtGui.QSpinBox(self) for l in self.labels]

        self.comboROI = QtGui.QComboBox(self)
        self.comboROI.addItems(["ROI H", "ROI V", "ROI Int"])
        self.grid.addWidget(self.comboROI, 7, 0)

        for i, (l, sb, sbv) in enumerate(zip(self.labels, self.spin_boxes,
                                             self.spinbox_values)):
            self.grid.addWidget(l, 3+i, 0)
            self.grid.addWidget(sb, 3+i, 1)
            sb.setMaximum(len(self.div_images))
            sb.setValue(sbv)

        self.comboROI.currentIndexChanged.connect(self.handleCurrentIndexChanged)
        sb.valueChanged.connect(self.handleSpinBoxValueChanged)
        self.updateCollage()

    def handleSpinBoxValueChanged(self, newValue):
        self.spinbox_values = [sb.value() for sb in self.spin_boxes]
        self.combo_index = self.comboROI.currentIndex()
        self.updateCollage()

    def handleCurrentIndexChanged(self, newIndex):
        self.updateCollage()

    def updateCollage(self):
        roi = self.rois[self.comboROI.currentIndex()]
        start_index, step_index, stop_index = [sb.value() for sb in
                                               self.spin_boxes]
        indices = np.arange(start_index, stop_index, step_index)
        sub_images = [getSubImage(self.div_images[i], roi) for i in indices]
        if roi[1] == 0:
            collage_image = np.vstack(sub_images)
        else:
            collage_image = np.hstack(sub_images)
        self.image_view.handleImageChanged(collage_image)
