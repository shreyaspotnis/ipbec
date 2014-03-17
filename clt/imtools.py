import numpy as np
from matplotlib.pyplot import imread
from repose_lru import lru_cache
import matplotlib.pyplot as plt


@lru_cache(maxsize=200)
def readImageFile(path):
        """Read .tif file and return numpy array with the image.

        This function is wrapped around a LRU cache. This means that
        images once read will be stored in a cache, so that subsequent
        calls to the function with the same filename will not result in
        disk IO.
        """
        Image = imread(path).T
        # most significant bit of all pixel data is 1, so we subtract it
        # no idea why, just found it by accident
        return np.array(Image - 2 ** 15, dtype=float)


def dividedImage(abs_image_, ref_image_, dark_image=None,
                 od_minmax=None):
        abs_image = np.array(abs_image_)
        ref_image = np.array(ref_image_)
        if dark_image is not None:
            abs_image -= dark_image
            ref_image -= dark_image
        # avoid a divide by zero, or taking a log of zero.
        abs_image = np.array((abs_image <= 0) * 1.0 + (abs_image > 0) * abs_image,
                            dtype=float)
        ref_image = np.array((ref_image <= 0) * 1.0 + (ref_image > 0) * ref_image,
                            dtype=float)
        divImage = np.log(ref_image / abs_image)

        if od_minmax is not None:
            minMask = divImage < od_minmax[0]
            maxMask = divImage > od_minmax[1]
            return (minMask * od_minmax[0] + maxMask * od_minmax[1] +
                    (~minMask & ~maxMask) * divImage)
        else:
            return divImage


def normalize(im, mask=None):
    if mask is None:
        return im / np.sum(im * im) ** 0.5
    else:
        return im / np.sum(im * im * mask) ** 0.5


def innerProduct(im1, im2, mask=None):
    if mask is None:
        return np.sum(im1 * im2)
    else:
        return np.sum(im1 * im2 * mask)


def projector(ofVector, onVector, mask=None):
    """read as projector of a Vector on a Vector. Assumes onVector is
    already normalized."""
    if mask is None:
        return innerProduct(ofVector, onVector) * onVector
    else:
        return innerProduct(ofVector, onVector, mask) * onVector
