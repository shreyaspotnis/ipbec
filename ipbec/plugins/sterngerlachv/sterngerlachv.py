from PyQt4 import uic
from PyQt4 import QtGui, QtCore
import pyqtgraph as pg
import os
import numpy as np


from ipbec.clt.imtools import getROISlice

curr_dir = os.path.dirname(os.path.abspath(__file__))
ui_file = os.path.join(curr_dir, "sterngerlach.ui")

Ui_PluginDialog, QDialog = uic.loadUiType(ui_file)


class PluginDialog(QDialog):

    """Handles the plugin dialogbox."""

    name = "Stern Gerlach V"

    def __init__(self, settings, data_dict):
        super(PluginDialog, self).__init__()
        self.settings = settings
        self.data_dict = data_dict
        div_images = self.data_dict['ref_images']
        self.n_images = len(div_images)

        div_image_1 = self.data_dict['div_images'][0]
        roi_v = self.data_dict['roi_v']
        indices, data = getROISlice(div_image_1, roi_v)
        self.max_length = len(data)

        self.settings.beginGroup('savedialog')
        self.save_folder = str(self.settings.value('save_folder', './').toString())
        self.settings.endGroup()

        self.grid = QtGui.QGridLayout(self)
        self.setLayout(self.grid)

        self.roiv_plot = pg.PlotWidget(title='ROI V', parent=self)
        self.grid.addWidget(self.roiv_plot, 0, 0, 1, 4)
        self.pData = self.roiv_plot.plot()  # to plot the data
        self.pData.setPen((255, 255, 255))
        self.div_pens = [self.roiv_plot.plot() for i in range(6)]
        for dp in self.div_pens:
            dp.setPen((255, 0, 0))

        self.offsetSpinBox = QtGui.QSpinBox(self)
        self.offsetSpinBox.setMaximum(self.max_length)
        self.offsetSpinBox.setValue(1)
        self.spacingSpinBox = QtGui.QSpinBox(self)
        self.spacingSpinBox.setMaximum(self.max_length)
        self.spacingSpinBox.setValue(1)
        self.resetButton = QtGui.QPushButton("Reset", self)
        self.resetButton.clicked.connect(self.handleReset)

        self.saveButton = QtGui.QPushButton("Save", self)
        self.saveButton.clicked.connect(self.handleSave)

        self.offsetLabel = QtGui.QLabel("Offset")
        self.widthLabel = QtGui.QLabel("Width")
        self.allLabel = QtGui.QLabel("All")

        self.tableWidget = QtGui.QTableWidget(self.n_images, 2, self)
        self.tableWidget.currentCellChanged.connect(self.handleCurrentCellChanged)
        self.tableWidget.cellChanged.connect(self.handleCellChanged)

        self.grid.addWidget(self.offsetLabel, 1, 1)
        self.grid.addWidget(self.widthLabel, 1, 2)

        self.grid.addWidget(self.allLabel, 2, 0)
        self.grid.addWidget(self.offsetSpinBox, 2, 1)
        self.grid.addWidget(self.spacingSpinBox, 2, 2)
        self.grid.addWidget(self.resetButton, 2, 3)
        self.grid.addWidget(self.saveButton, 3, 3)
        self.grid.addWidget(self.tableWidget, 3, 1, 1, 2)

        self.handleReset()

    def handleReset(self):
        self.tableWidget.currentCellChanged.disconnect(self.handleCurrentCellChanged)
        self.tableWidget.cellChanged.disconnect(self.handleCellChanged)
        offset = self.offsetSpinBox.value()
        spacing = self.spacingSpinBox.value()
        for i in range(self.n_images):
            self.tableWidget.setItem(i, 0,
                                     QtGui.QTableWidgetItem(str(offset)))
            self.tableWidget.setItem(i, 1,
                                     QtGui.QTableWidgetItem(str(spacing)))
        self.tableWidget.currentCellChanged.connect(self.handleCurrentCellChanged)
        self.tableWidget.cellChanged.connect(self.handleCellChanged)
        self.handleCellChanged(0, 0)

    def handleCurrentCellChanged(self, row, col, prev_row, prev_col):
        self.handleCellChanged(row, col)

    def handleCellChanged(self, row, col):
        div_image = self.data_dict['div_images'][row]
        roi_v = self.data_dict['roi_v']
        indices, data = getROISlice(div_image, roi_v)
        offset = int(self.tableWidget.item(row, 0).text())
        spacing = int(self.tableWidget.item(row, 1).text())
        self.plotProfile(data, offset, spacing)

    def plotProfile(self, data, offset, spacing):
        x_indices = np.arange(len(data))
        max_val = np.max(data)
        self.pData.setData(x=x_indices, y=data)
        for i, dp in enumerate(self.div_pens):
            xval = offset + i*spacing
            dp.setData([xval, xval], [0, max_val])

    def handleSave(self):
        offsets = [int(self.tableWidget.item(i, 0).text())
                   for i in range(self.n_images)]
        spacings = [int(self.tableWidget.item(i, 1).text())
                    for i in range(self.n_images)]
        div_images = self.data_dict['div_images']
        roi_v = self.data_dict['roi_v']
        data_slices = [getROISlice(di, roi_v)[1] for di in div_images]
        populations = np.array([self.getPopulations(ds, off, spa)
                                for (ds, off, spa) in zip(data_slices,
                                                          offsets,
                                                          spacings)])
        save_dialog = QtGui.QFileDialog.getSaveFileName
        file_name = str(save_dialog(self, caption='Save as...',
                                    directory=self.save_folder))
        if file_name != '':
            header_string = 'mF=-2\t mF=-1\tmF=0\t mF=1\tmF=2'
            np.savetxt(file_name, populations, delimiter='\t',
                       header=header_string)

    def getPopulations(self, data_slice, offset, spacing):
        pops = np.array([np.sum(data_slice[(offset+i*spacing):(offset+(i+1)*spacing)])
                         for i in range(5)])
        return pops/np.sum(pops)
