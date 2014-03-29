import numpy as np
from matplotlib.pyplot import imread
from repose_lru import lru_cache


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


def basisList(ref_images):
    for i, rI in enumerate(ref_images):
        if i is 0:
            basis = [rI]
        else:
            current = np.array(rI)
            for b in basis:
                current -= projector(rI, b)
            basis.append(normalize(current))
    return basis


def generateBasis(ref_images):
    """Generator for a list of orthonormal basis images based on images
    supplied in ref_images."""
    for i, rI in enumerate(ref_images):
        print(i)
        if i is 0:
            basis = [ref_images[0]]
        else:
            current = np.array(rI)
            for b in basis:
                current -= projector(rI, b)
            basis.append(normalize(current))
        yield basis[i]


def generateCleanRefs(abs_images, basis, mask):
    """Generator for clean refs for all absoprtion images. Uses basis to
    reconstruct ideal absoprtion image."""
    for aI in abs_images:
        current = np.zeros(aI.shape, dtype=float)
        for b in basis:
            current += projector(aI, b, mask)
        # normalize correctly
        absLength = innerProduct(aI, aI, mask)
        currLength = innerProduct(current, current, mask)
        multFactor = np.sqrt(absLength/currLength)
        current *= multFactor
        yield current


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


def getSensibleROI(roi, im_shape):
    (x1, y1, x2, y2) = roi[0]
    (xm, ym) = im_shape

    x1c = max(int(min(x1, x2)), 0)
    x2c = min(int(max(x1, x2)), xm)
    y1c = max(int(min(y1, y2)), 0)
    y2c = min(int(max(y1, y2)), ym)

    return ([x1c, y1c, x2c, y2c], roi[1])


def getROISlice(im, roi):
    """Returns a 1d slice of the image within the ROI.

    roi is a list:
    roi = [(x1, y1, x2, y2), axis]

    (x1, y1) are the indices of the top left corner.
    (x2, y2) for the bottom right. The index itself is not included.

    axis is direction of averaging.
    """
    roi1 = getSensibleROI(roi, im.shape)
    (x1, y1, x2, y2) = roi1[0]

    if roi[1] is 0:
        indices = np.arange(y1, y2)
    else:
        indices = np.arange(x1, x2)

    sub_im = im[x1:x2, y1:y2]

    return (indices, np.mean(sub_im, axis=roi[1]))
