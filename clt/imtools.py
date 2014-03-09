import numpy as np
from matplotlib.pyplot import imread


def readImageFile(path):
        """Read .tif file and return numpy array with the image."""
        Image = imread(path).T
        # most significant bit of all pixel data is 1, so we subtract it
        # no idea why, just found it by accident
        return np.array(Image - 2 ** 15, dtype=float)
