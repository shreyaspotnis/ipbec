from PyQt4 import QtGui, QtCore
import pyqtgraph as pg


class ImageItem(pg.ImageItem):
    """Custom ImageItem to handle single and double clicks.

    This widget displays the actual image inside an imageView class"""

    doubleClicked = QtCore.pyqtSignal(tuple)
    singleClicked = QtCore.pyqtSignal(tuple)

    def __init__(self, *args, **kwds):
        super(ImageItem, self).__init__(*args, **kwds)
        pass

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit((event.pos().x(), event.pos().y()))

    def mouseClickEvent(self, event):
        self.singleClicked.emit((event.pos().x(), event.pos().y()))


class ImageView(pg.ImageView):

    doubleClicked = QtCore.pyqtSignal(tuple)
    singleClicked = QtCore.pyqtSignal(tuple)

    def __init__(self, settings, parent=None):
        self.imageItem = ImageItem()
        super(ImageView, self).__init__(parent=parent, name='BEC',
                                          imageItem=self.imageItem)
        self.imageItem.singleClicked.connect(self.singleClicked)
        self.imageItem.doubleClicked.connect(self.doubleClicked)
