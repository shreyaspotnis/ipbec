import pyqtgraph as pg
import numpy as np


class Plot1d(pg.PlotWidget):
    """Widget for plotting 1d data and fits to it."""

    def __init__(self, parent=None, title='Plot1d'):
        super(Plot1d, self).__init__(title=title, parent=parent)

        self.pData = self.plot()  # to plot the data
        self.pData.setPen((255, 255, 255))

        self.pFit = self.plot()  # to plot fits
        self.pFit.setPen((255, 0, 0))

    def handleDataChanged(self, data, fit):
        self.pData.setData(y=data)

        if fit is None:
            self.pFit.setData(y=np.array([]))
        else:
            self.pFit.setData(fit)
