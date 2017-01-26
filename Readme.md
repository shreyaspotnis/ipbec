#IP-BEC

![Screenshot of the GUI analyze absorption images](docs/screenshot.png?raw=true "IP-BEC GUI")

IP-BEC (IP stands for image processing) is a PyQt4 application to analyze
absorption images of Bose-Einstein Condensates. It is GUI based, but all the
image browsing, image processing and fitting subroutines are available as
python modules which can be used for scripting. Some of the features
implemented in the software include adding tags and comments to absorption
images, fringe reduction using the eigen-face algorithm, correcting for
saturation due to high probe intensity, fitting the 2D column density to
various functions. Additional features are added via plugins, which themselves
are python modules so that they can be reused in external scripts.


## Requirements
IP-BEC is written in PyQt4 and uses pyqtgraph for plotting. Hence, it is
completely cross-platform. It has been tested on Windows, Mac and Linux using
python 2.7. The following python packages are required:

- [PyQt4](https://www.riverbankcomputing.com/software/pyqt/download)
- [pyqtpgraph](http://www.pyqtgraph.org/)
- [numpy](http://www.numpy.org/)
- [pillow](https://python-pillow.org/)


## Installation

```bash
pip install ipbec
```

If you wish to modify the code, download the package in a local directory
and install it in develop mode.

```bash
cd path/to/installation
git clone https://github.com/shreyaspotnis/ipbec
cd ipbec
python setup.py develop
```

## Running

Before running for the first time, you need to create an empty JSON database.
Create a file with only
```
{}
```
in it. Then run ipbec:

```bash
python -m ipbec

```


## Features

- Watches a directory and automatically updates as new images are acquired.
- Fitting to 2D distributions. Can easily add more fitting functions.
- Fringe reduction.
- Correction for probe detuning, high probe intensity, correction for
non-resonant light.
- Extensible: support for plugins.
- Tagging of images.

## Usage

IP-BEC works by watching a directory for new images. As absorption images are
acquired, they are added to this directory. For IPBEC to work for your setup,
two things need to be changed.

First, modify the function `readImageFile` in
`ipbec/clt/imtools.py` so that it reads your image format of choice and converts
it into a numpy array.

Second, modify the `ImageList` class in `clt/ImageList.py` to suit your
file naming format. The way it's done currently is for every absorption image,
two new images are added. The first is an absorption image, and the second
is a reference image. The absorption image ends with `'Abs.tif'` and the reference
image ends with `'Ref.tif'`. Check out `/ipbec/testdata/test_images` for some
sample images.
