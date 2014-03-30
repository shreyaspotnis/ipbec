from PyQt4.QtGui import QWidget, QGridLayout, QLabel, QDoubleSpinBox
import numpy as np
from clt import imtools


class Analyzer(QWidget):
    """Widget to analyze fit data. Extract relevant parameters."""

    Inputs = ['TOF(ms)', 'Pixel Size(um)', 'Detuning(MHz)',
              'Exposure Time (us)', 'Probe Intensity/I0', 'fx(Hz)', 'fy(Hz)',
              'fz(Hz)']
    Outputs = ['Fitted Atom Number', 'Integrated Atom Number', 'H Temp(uK)',
               'V Temp(uK)', 'Peak Density(cm^-3)', 'Collision Rate',
               'BEC Fraction', 'Chemical potential(nK)']
    OutputFormats = ['%.2e', '%.2e', '%.2g', '%.2g', '%g', '%g', '%.3g',
                     '%.1g']

    def __init__(self, settings, parent=None):
        super(Analyzer, self).__init__(parent)
        self.parent = parent
        self.settings = settings
        self.initialized = False
        self.has_roi_h = False
        self.has_roi_v = False
        self.has_roi_int = False

    def initUI(self):
        self.grid = QGridLayout(self)
        self.setLayout(self.grid)

        self.loadSettings()
        self.inputLabels = [QLabel(l) for l in self.Inputs]
        self.inputBoxes = []
        for i, iL in enumerate(self.inputLabels):
            self.grid.addWidget(iL, i, 0)

            sp = QDoubleSpinBox(self)
            sp.setRange(-1e10, 1e10)
            sp.setKeyboardTracking(False)
            self.grid.addWidget(sp, i, 1)
            self.inputBoxes.append(sp)

        for val, iB in zip(self.inputValues, self.inputBoxes):
            iB.setValue(val)
        self.connectSpinBoxes()

        self.outputValues = [0.0]*len(self.Outputs)
        self.outputLabels = [QLabel(l) for l in self.Outputs]
        self.outputValueLabels = [QLabel('0.0') for l in self.Outputs]

        sI = len(self.inputLabels)
        for i, oL in enumerate(self.outputLabels):
            self.grid.addWidget(oL, sI + i, 0)
            self.grid.addWidget(self.outputValueLabels[i], sI + i, 1)

    def handleImageChanged(self, new_image_info):
        self.image_info = new_image_info
        if not self.initialized:
            self.initUI()
            self.initialized = True
        self.updateOutputValues(fit_type=None)

    def handleDoneFitting(self, fit_type):
        self.updateOutputValues(fit_type=fit_type)

    def handleInputValueChanged(self, new_value):
        self.inputValues = [float(sp.value()) for sp in self.inputBoxes]
        self.updateOutputValues()

    def connectSpinBoxes(self):
        for sp in self.inputBoxes:
            sp.valueChanged.connect(self.handleInputValueChanged)

    def loadSettings(self):
        self.settings.beginGroup('analyzer')
        self.inputValues = []
        for il in self.Inputs:
            val = self.settings.value(il, type=float, defaultValue=0.0)
            self.inputValues.append(val)

        self.settings.endGroup()

    def saveSettings(self):
        self.settings.beginGroup('analyzer')
        for il, iv in zip(self.Inputs, self.inputValues):
            self.settings.setValue(il, iv)
        self.settings.endGroup()

    def handleROIHChanged(self, new_roi):
        self.has_roi_h = True
        self.roi_h = new_roi

    def handleROIVChanged(self, new_roi):
        self.has_roi_v = True
        self.roi_v = new_roi

    def handleROIIntChanged(self, new_roi):
        self.has_roi_int = True
        self.roi_int = new_roi
        self.updateOutputValues(fit_type=None)

    def updateOutputValues(self, fit_type=None):
        (tof, ps, det, ex_time, Ip, fx, fy, fz) = self.inputValues
        im = self.image_info[self.image_info['image_type']]

        kb = 1.3806e-23         # (SI) Boltzman constant
        m_rb = 1.443e-25         # (kg) Mass of Rubiduim87

        sigma_23 = 2.906692e-9  # cm^2
        Isat_23 = 1.66933  # mW/cm^2
        pi = 3.1415926
        gamma = 6.0666  # MHz

        det_hl = 2.0*det/gamma  # deturning in half linewidths
        OD_to_atom_number = ps**2*1e-8*(1 + det_hl**2)/sigma_23

        if self.has_roi_int:
            ODsum = np.sum(imtools.getSubImage(im, self.roi_int))
        else:
            ODsum = 0
        Ni = ODsum*OD_to_atom_number

        if fit_type is None:
            # just update integrated atom number
            self.outputValues[1] = Ni
            self.outputValueLabels[1].setText(self.OutputFormats[1] % Ni)
            return

        # if fit_type == 'Gauss2D':
        #     (height, xc, yc, xw, yw, offset) = fitParms
        #     # find integrated OD_i, OD_i = integral (OD dx dy)
        #     OD_i = height*(2.0*pi*xw*yw)
        #     Nf = OD_i*(1 + det_hl**2)/sigma_23
        #     T_H = ((xw*ps*1e-6)/(tof*1e-3))**2*m_rb/kb*1e6
        #     T_V = ((yw*ps*1e-6)/(tof*1e-3))**2*m_rb/kb*1e6
        #     bec_fraction = 0.0
        #     mu = 0  # don't caluclate for Gauss2D

        # elif fit_type == 'Thomas Fermi 2D':
        #     (height, xc, yc, rx, ry, offset) = fitParms
        #     OD_i = height*(pi*rx*ry/2.0)
        #     T_H = 0
        #     T_V = 0
        #     bec_fraction = 1.0
        #     mu = 0  # TODO: calculate mu later on

        # elif fit_type == 'TF + Gauss2D':
        #     (h_tf, h_g, cx, cy, rx, ry, wx, wy, offset) = fitParms
        #     OD_tf = h_tf*(pi*rx*ry/2.0)
        #     OD_gauss = h_g*(2.0*pi*wx*wy)
        #     OD_i = OD_tf + OD_gauss
        #     T_H = ((wx*ps*1e-6)/(tof*1e-3))**2*m_rb/kb*1e6
        #     T_V = ((wy*ps*1e-6)/(tof*1e-3))**2*m_rb/kb*1e6
        #     bec_fraction = OD_tf/OD_i
        #     mu = 0  # calculate mu later on

        # # do your calculations here
        # # ps = pixel size in microns, 1e-8 converts to cm^2
        # Nf = OD_i*OD_to_atom_number

        # self.outputValues = [Nf, Ni, T_H, T_V, 0, 0, bec_fraction, mu]
        # for ov, ovl, ovf in zip(self.outputValues, self.outputValueLabels,
        #                         self.OutputFormats):
        #     ovl.setText(ovf % ov)
