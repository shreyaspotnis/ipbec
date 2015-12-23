#IP-BEC

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
completely cross-platform. The following python packages are required:

- [PyQt4](https://www.riverbankcomputing.com/software/pyqt/download)
- [pyqtpgraph](http://www.pyqtgraph.org/)
- [numpy](http://www.numpy.org/)


## Installation

```bash
pip install ipbec
```

## Running

```bash
python -m ipbec

```

