from PyQt4.QtGui import QWidget, QGridLayout, QLabel, QDoubleSpinBox
import numpy as np
from ipbec.clt import imtools
from ipbec.clt import fittools


class Analyzer(QWidget):
    """Widget to analyze fit data. Extract relevant parameters."""

    Inputs = ['TOF(ms)', 'Pixel Size(um)', 'Detuning(MHz)',
              'Exposure Time (us)', 'Probe Intensity/I0', 'fx(Hz)', 'fy(Hz)',
              'fz(Hz)']
    Outputs = ['Fitted Atom Number', 'Integrated Atom Number', 'H Temp(uK)',
               'V Temp(uK)', 'Peak Density(cm^-3)', 'Collision Rate',
               'BEC Fraction', 'Chemical potential(nK)', 'Int Number H',
               'Int Number V', 'NH/(NH+NV)', '<x>', '<x2>', '<delx>',
               '<y>', '<y2>', '<dely>']
    OutputFormats = ['%.2e', '%.2e', '%.2g', '%.2g', '%g', '%g', '%.3g',
                     '%.1f', '%.2e', '%.2e', '%.3e', '%3.1f', '%3.1f', '%3.1f',
                     '%3.1f', '%3.1f', '%3.1f', ]

    def __init__(self, settings, parent=None):
        super(Analyzer, self).__init__(parent)
        self.parent = parent
        self.settings = settings
        self.initialized = False
        self.has_roi_h = False
        self.has_roi_v = False
        self.has_roi_int = False
        self.has_fitted_stuff = False

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
        self.has_fitted_stuff = False
        self.updateOutputValues()

    def handleDoneFitting(self, fit_type):
        self.has_fitted_stuff = True
        self.fit_type = fit_type
        self.updateOutputValues()

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
        self.updateOutputValues()

    def handleROIVChanged(self, new_roi):
        self.has_roi_v = True
        self.roi_v = new_roi
        self.updateOutputValues()

    def handleROIIntChanged(self, new_roi):
        self.has_roi_int = True
        self.roi_int = new_roi
        self.updateOutputValues()

    def updateOutputValues(self):
        (tof, ps, det, ex_time, Ip, fx, fy, fz) = self.inputValues
        im = self.image_info[self.image_info['image_type']]


        kb = 1.3806e-23         # (SI) Boltzman constant
        m_rb = 1.443e-25         # (kg) Mass of Rubiduim87

        sigma_23 = 2.906692e-9  # cm^2
        # sigma_22 =
        Isat_23 = 1.66933  # mW/cm^2
        pi = 3.1415926
        gamma = 6.0666  # MHz

        det_hl = 2.0*det/gamma  # deturning in half linewidths
        # ps = pixel size in microns, 1e-8 converts to cm^2
        OD_to_atom_number = ps**2*1e-8*(1 + det_hl**2)/sigma_23

        if self.has_roi_int:
            ODsum = np.sum(imtools.getSubImage(im, self.roi_int))
            (x_ex, x2_ex, delx_ex,
             y_ex, y2_ex, dely_ex) = imtools.getExpectationValues(im,
                                                                  self.roi_int)
        else:
            ODsum = 1e-30
            x_ex = 0
            x2_ex = 0
            y_ex = 0
            y2_ex = 0
            delx_ex = 0
            dely_ex = 0

        if self.has_roi_h:
            ODsum_h = np.sum(imtools.getSubImage(im, self.roi_h))
        else:
            ODsum_h = 1e-30

        if self.has_roi_v:
            ODsum_v = np.sum(imtools.getSubImage(im, self.roi_v))
        else:
            ODsum_v = 1e-30

        Ni = ODsum*OD_to_atom_number
        Nih = ODsum_h*OD_to_atom_number
        Niv = ODsum_v*OD_to_atom_number
        Nh_over_Nv = Nih / (Nih + Niv)

        if self.has_fitted_stuff is False:
            # update all values that do not require fitted data
            indices = [1, 8, 9, 10, 11, 12, 13, 14, 15, 16]
            values = [Ni, Nih, Niv, Nh_over_Nv, x_ex, x2_ex, delx_ex, y_ex,
                      y2_ex, dely_ex]
            for i, v in zip(indices, values):
                self.outputValues[i] = v
                self.outputValueLabels[i].setText(self.OutputFormats[i] % v)
            return

        # else update everything

        save_dict = self.image_info['save_info']
        fit_dict = save_dict['fitter'][self.fit_type]
        fit_parms = fittools.dictToList(fit_dict['parms'], self.fit_type)

        if self.fit_type == 'Gauss2D':
            (height, xc, yc, xw, yw, offset) = fit_parms
            # find integrated OD_i, OD_i = integral (OD dx dy)
            OD_i = height*(2.0*pi*xw*yw)
            Nf = OD_i*(1 + det_hl**2)/sigma_23
            # factor of 2 in the end, as gaussian width is not defined the
            # standard way. Check out definition in fittools.py
            T_H = ((xw*ps*1e-6)/(tof*1e-3))**2*m_rb/kb*1e6/2.0
            T_V = ((yw*ps*1e-6)/(tof*1e-3))**2*m_rb/kb*1e6/2.0
            bec_fraction = 0.0
            mu = 0  # don't caluclate for Gauss2D

        elif self.fit_type == 'Thomas Fermi 2D':
            (height, xc, yc, rx, ry, offset) = fit_parms
            OD_i = height*(pi*rx*ry/2.0)
            T_H = 0
            T_V = 0
            bec_fraction = 1.0
            mu = 0  # TODO: calculate mu later on

        elif self.fit_type == 'TF + Gauss2D':
            (h_tf, h_g, cx, cy, rx, ry, wx, wy, offset) = fit_parms
            OD_tf = h_tf*(pi*rx*ry/2.0)
            OD_gauss = h_g*(2.0*pi*wx*wy)
            OD_i = OD_tf + OD_gauss
            T_H = ((wx*ps*1e-6)/(tof*1e-3))**2*m_rb/kb*1e6/2.0
            T_V = ((wy*ps*1e-6)/(tof*1e-3))**2*m_rb/kb*1e6/2.0
            bec_fraction = OD_tf/OD_i
            mu = 0  # calculate mu later on

        elif self.fit_type == 'TFInt + BoseEnhanced':
            (h_tf, h_g, cx, cy, rx, ry, wx, wy, offset) = fit_parms
            OD_tf = h_tf*(2.0*pi*rx*ry/5.0)
            OD_gauss = h_g*(2.0*pi*wx*wy)
            OD_i = OD_tf + OD_gauss
            T_H = ((wx*ps*1e-6)/(tof*1e-3))**2*m_rb/kb*1e6
            T_V = ((wy*ps*1e-6)/(tof*1e-3))**2*m_rb/kb*1e6
            bec_fraction = OD_tf/OD_i
            mu = 0  # calculate mu later on

        elif self.fit_type == 'TF Int':
            (height, xc, yc, rx, ry, offset) = fit_parms
            OD_i = height*(2.0*pi*rx*ry/5.0)
            T_H = 0
            T_V = 0
            bec_fraction = 1.0
            mu = 0  # TODO: calculate mu later on
            ###########################
            ###########################
            # changed it from
            mu = (ry*ps*1e-6/tof/1e-3) ** 2 * 2.0 / 7.0 * (m_rb/kb*1e9)
        elif self.fit_type == 'Double Gauss 2D':
            # parameterNames = ['Height 1', 'X Center 1', 'Y Center 1', 'X Width 1',
            #           'Y Width 1', 'Height 2', 'X Center 2', 'Y Center 2',
            #           'X Width 2', 'Y Width 2', 'Offset']
            (h1, xc1, yc1, xw1, yw1, h2, xc2, yc2, xw2, yw2, offset) = fit_parms
            OD_i = h1*(2.0*pi*xw1*yw1) + h2*(2.0*pi*xw2*yw2)
            T_H = 0
            T_V = 0
            bec_fraction = 0.0


        # do your calculations here
        Nf = OD_i*OD_to_atom_number

        self.outputValues = [Nf, Ni, T_H, T_V, 0, 0, bec_fraction, mu, Nih,
                             Niv, Nh_over_Nv, x_ex, x2_ex, delx_ex, y_ex,
                             y2_ex, dely_ex]
        for ov, ovl, ovf in zip(self.outputValues, self.outputValueLabels,
                                self.OutputFormats):
            ovl.setText(ovf % ov)

        # Save all analyzed stuff

        if 'analyzer' not in save_dict:
            save_dict['analyzer'] = {}
        sub_dict = save_dict['analyzer'][self.fit_type] = {}
        sub_dict['output'] = dict(zip(self.Outputs, self.outputValues))
        sub_dict['inputs'] = dict(zip(self.Inputs, self.inputValues))
