from PyQt4 import QtCore
import pyqtgraph as pg

# If the following line is not included, pyqtgraph crashes. Bug which is
# already fixed in subsequent releases of pyqtgraph.
# https://groups.google.com/forum/#!msg/pyqtgraph/O7E2sWaEWDg/7KPVeiO6qooJ
pg.functions.USE_WEAVE = False


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

    # def handleMainImageChanged(self, image_info):
    #     im = image_info[image_info['image_type']]

    #     self.setImage(im)
    #     # super(ImageView, self).setImage(im)

    def handleImageChanged(self, new_image):
        self.setImage(new_image)
