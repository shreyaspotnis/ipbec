import numpy as np
from scipy import optimize
import time
import pprint


class Fitter(object):
    """Generic class for a fitting function. Every fitting class should have
    the following functions"""

    name = 'Fitter'
    parameterNames = ['p1', 'p2']

    def __init__(self, im=None):
        self.im = im

        # add names to parameters

        self.fitParameters = [0.0, 0.0]
        self.fitParmSD = [0.0, 0.0]
        self.guess = [0.0, 0.0]
        self.hasGuessed = False

    def updateImage(self, im, keepGuess=False):
        self.im = im
        if keepGuess is False:
            self.hasGuessed = False
        else:
            self.hasGuessed = True

    def autoGuess(self):
        self.hasGuessed = True

    def setGuess(self, guess):
        self.guess = guess
        self.hasGuessed = True

    def setGuessCenter(self, pos):
        pass

    def fitFunction(self, parms):
        pass

    def fit(self, maxfev=0, roi=None):
        """Returns the parameters of found by a fit"""
        if not self.hasGuessed:
            self.autoGuess()
        start_time = time.time()
        X, Y = np.indices(self.im.shape)
        if roi is not None:
            Xs = X[roi[0]:roi[2], roi[1]:roi[3]]
            Ys = Y[roi[0]:roi[2], roi[1]:roi[3]]
            ims = self.im[roi[0]:roi[2], roi[1]:roi[3]]
        else:
            Xs, Ys, ims = X, Y, self.im
        errorfunction = lambda p: np.ravel(self.fitFunction(*p)(Xs, Ys) - ims)
        output = optimize.leastsq(errorfunction, self.guess, full_output=1,
                                  maxfev=maxfev)
        time_diff = time.time() - start_time
        (p, cov_p, info_dict, mesg, ier) = output
        if cov_p is not None:
            residue = errorfunction(p)
            s_sq = (residue**2).sum()/(len(residue)-len(p))
            cov_p *= s_sq
            self.fitParmSD = np.abs(np.diag(cov_p)) ** 0.5
        else:
            # this means that the fit has failed. Ignore s_sq
            s_sq = 0
        self.fitParameters = p

        return output + (s_sq, time_diff)

    def printParameters(self):
        for pn, fp in zip(self.parameterNames, self.fitParameters):
            print(pn, fp)

    def fittedData(self):
        ff = self.fitFunction(*self.fitParameters)
        X, Y = np.indices(self.im.shape)
        return ff(X, Y)

    def guessData(self):
        ff = self.fitFunction(*self.guess)
        X, Y = np.indices(self.im.shape)
        return ff(X, Y)


class Gauss2D(Fitter):
    """Fitter class for a 2D Gaussian"""

    name = 'Gauss2D'
    parameterNames = ['Height', 'X Center', 'Y Center', 'X Width',
                      'Y Width', 'Offset']

    def __init__(self, im=None):
        super(Gauss2D, self).__init__(im)

        self.fitParameters = [0.0, 0.0, 0.0, 1.0, 1.0, 0.0]
        self.fitParmSD = [0.0, 0.0, 0.0, 1.0, 1.0, 0.0]
        self.guess = [0.0, 0.0, 0.0, 1.0, 1.0, 0.0]

    def autoGuess(self):
        """Returns (height, x, y, width_x, width_y, offset)
        the gaussian parameters of a 2D distribution by calculating its
        moments. Note: autoguessing needs to get smarter. Doesn't work for a
        lot of cleaned images, dunno why"""
        super(Gauss2D, self).autoGuess()
        data = abs(self.im)
        total = data.sum()
        X, Y = np.indices(data.shape)
        x = (X * data).sum() / total
        y = (Y * data).sum() / total
        # >>> i,j = np.unravel_index(a.argmax(), a.shape)
        height = data.max()
        offset = data.mean()

        x, y = np.unravel_index(data.argmax(), data.shape)

        # hack to get a right width -
        # ignore data which is less than 1/e^2 of the max
        # this is because noise will contribute to the variance,
        # giving a higher width than expected. Any offset will also
        # contribute to increasing the width, since we are taking the
        # absolute of the data
        em2 = height * np.exp(-2)
        col = data[:, int(y)]
        col *= col > em2
        xarray = np.arange(col.size)

        row = data[int(x), :]
        row *= row > em2
        yarray = np.arange(row.size)

        width_x = np.sqrt(((xarray - x) ** 2 * col).sum() / col.sum())
        width_y = np.sqrt(((yarray - y) ** 2 * row).sum() / row.sum())

        self.guess = [height, x, y, width_x, width_y, offset]

        return self.guess

    def fitFunction(self, height, center_x, center_y,
                    width_x, width_y, offset):
        """Returns a gaussian function with the given parameters"""
        width_x = float(width_x)
        width_y = float(width_y)
        return lambda x, y: offset + height * np.exp(
                            -(((center_x - x)/width_x) ** 2
                                + ((center_y - y)/ width_y) ** 2) / 2.0)

    def setGuessCenter(self, pos):
        self.guess[1:3] = pos

    def fit(self, maxfev=0, roi=None):
        p = super(Gauss2D, self).fit(maxfev=maxfev, roi=roi)
        # make widths always positive
        self.fitParameters[3] = abs(self.fitParameters[3])
        self.fitParameters[4] = abs(self.fitParameters[4])
        return p


class TF2D(Gauss2D):
    """Fitter class for a 2D Thomas Fermi profile"""

    name = 'Thomas Fermi 2D'
    parameterNames = ['Height', 'X Center', 'Y Center', 'X Radius',
                      'Y Radius', 'Offset']

    def __init__(self, im=None):
        super(TF2D, self).__init__(im)

    def fitFunction(self, height, cx, cy, rx, ry, offset):
        """Returns a gaussian function with the given parameters"""

        def isG0(a):
            """Zeroes all elements of the matrix less than 0."""
            return a * (a > 0)

        return lambda x, y: (isG0(height * (1 - ((x - cx) / rx)**2
                             - ((y-cy) / ry) ** 2)) + offset)


class TFGauss2D(Gauss2D):
    """Fitter class for a 2D Thomas Fermi profile"""

    name = 'TF + Gauss2D'
    parameterNames = ['TF Height', 'Gauss Height', 'X Center', 'Y Center',
                      'TF X Radius', 'TF Y Radius', 'Gauss X Width',
                      'Gauss Y Width', 'Offset']

    def __init__(self, im=None):
        super(TFGauss2D, self).__init__(im)

        self.fitParameters = [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0]
        self.fitParmSD = [0.0] * len(self.parameterNames)
        self.guess = [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0]

    def autoGuess(self):
        gaussGuess = super(TFGauss2D, self).autoGuess()
        # guess the initial parameters by fitting it to a gaussian first
        (height, center_x, center_y,
         width_x, width_y, offset) = gaussGuess
        # use this to guess initial parameters for the new fit
        self.guess = [height, height/2.0, center_x, center_y,
                      width_x*2.0, width_y*2.0, width_x*2.0, width_y*2.0,
                      offset]
        return self.guess

    def fitFunction(self, h_tf, h_g, cx, cy, rx, ry, wx, wy, offset):
        """Returns a gaussian function with the given parameters"""

        def isG0(a):
            """Zeroes all elements of the matrix less than 0."""
            return a * (a > 0)

        return lambda x, y: ((isG0(h_tf * (1 - ((x - cx) / rx)**2
                             - ((y-cy) / ry) ** 2))) +
                             h_g * np.exp(-(((cx - x)/wx) ** 2
                                          + ((cy - y) / wy) ** 2) / 2.0) +
                             offset)


class DoubleGauss2D(Gauss2D):

    name = 'Double Gauss 2D'
    parameterNames = ['Height 1', 'X Center 1', 'Y Center 1', 'X Width 1',
                      'Y Width 1', 'Height 2', 'X Center 2', 'Y Center 2',
                      'X Width 2', 'Y Width 2', 'Offset']

    def __init__(self, im=None):
        super(DoubleGauss2D, self).__init__(im)

        self.fitParameters = [0]*len(self.parameterNames)
        self.fitParmSD = [0.0] * len(self.parameterNames)
        self.guess = [0]*len(self.parameterNames)

    def autoGuess(self):
        gaussGuess = super(DoubleGauss2D, self).autoGuess()
        # guess the initial parameters by fitting it to a gaussian first
        (height, center_x, center_y,
         width_x, width_y, offset) = gaussGuess

        width_x = float(width_x)
        width_y = float(width_y)
        # use this to guess initial parameters for the new fit
        self.guess = [height, center_x, center_y, width_x, width_y,
                      height*0.5, center_x, center_y, width_x*2.0,
                      width_y*2.0, offset]
        return self.guess

    def fitFunction(self, h1, cx1, cy1, wx1, wy1,
                    h2, cx2, cy2, wx2, wy2, offset):
        """Returns a gaussian function with the given parameters"""

        def isG0(a):
            """Zeroes all elements of the matrix less than 0."""
            return a * (a > 0)

        return lambda x, y: (offset + h1*np.exp(-(((cx1 - x)/wx1)**2
                                                + ((cy1 - y)/wy1)**2)/2.0)
                             + h2*np.exp(-(((cx2 - x)/wx2)**2
                                         + ((cy2 - y)/wy2)**2)/2.0))


fittypes = [Gauss2D, TF2D, TFGauss2D, DoubleGauss2D]

fit_types_dict = {}
for f in fittypes:
    fit_types_dict[f.name] = f


def dictToList(fit_parms_dict, fit_type):
    for ft in fittypes:
        if ft.name == fit_type:
            l = [fit_parms_dict[key] for key in ft.parameterNames]
            return l
    else:
        raise ValueError(fit_type + ' is not a valid fit type')
