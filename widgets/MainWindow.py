from PyQt4 import uic
from pyqtgraph.dockarea import DockArea, Dock
from widgets import ImageView, ImageBrowser, Fitter

Ui_MainWindow, QMainWindow = uic.loadUiType("ui/MainWindow.ui")


class MainWindow(QMainWindow, Ui_MainWindow):
    """Where all the action happens."""

    def __init__(self, settings):
        super(MainWindow, self).__init__()
        self.settings = settings
        self.setupUi(self)

        # MainWindow is a collection of widgets in their respective docks.
        # We make DockArea our central widget
        self.dock_area = DockArea()
        self.setCentralWidget(self.dock_area)

        self.createDocks()
        self.initAfterCreatingDockWidgets()
        self.loadSettings()

        self.connectSignalsToSlots()

        # all signals in place, send out the first image
        self.image_browser.populateAndEmitImageInfo()

    def createDocks(self):
        """Create all dock widgets and add them to DockArea."""
        self.image_view = ImageView(self.settings, self)
        self.image_browser = ImageBrowser(self.settings, self)
        self.fitter = Fitter(self.settings, self)

        self.dock_image_view = Dock('Image View', widget=self.image_view)
        self.dock_image_browser = Dock('Image Browser',
                                       widget=self.image_browser)
        self.dock_fitter = Dock('Fitter', widget=self.fitter)

        self.dock_area.addDock(self.dock_image_view, position='top')
        self.dock_area.addDock(self.dock_image_browser, position='right',
                               relativeTo=self.dock_image_view)
        self.dock_area.addDock(self.dock_fitter, position='left',
                               relativeTo=self.dock_image_view)

    def initAfterCreatingDockWidgets(self):
        self.setWindowTitle(self.image_browser.current_directory)

    def connectSignalsToSlots(self):
        self.actionOpen_Directory.triggered.connect(self.image_browser.handleOpenDirectoryAction)
        self.actionDark_File.triggered.connect(self.image_browser.handleDarkFileAction)
        self.actionRefresh.triggered.connect(self.image_browser.handleRefreshAction)

        self.image_browser.windowTitleChanged.connect(self.setWindowTitle)
        self.image_browser.imageChanged.connect(self.image_view.handleImageChanged)

    def loadSettings(self):
        """Load window state from self.settings"""

        self.settings.beginGroup('mainwindow')
        geometry = self.settings.value('geometry').toByteArray()
        state = self.settings.value('windowstate').toByteArray()
        dock_string = str(self.settings.value('dockstate').toString())
        if dock_string is not "":
            dock_state = eval(dock_string)
            self.dock_area.restoreState(dock_state)
        self.settings.endGroup()

        self.restoreGeometry(geometry)
        self.restoreState(state)

    def saveSettings(self):
        """Save window state to self.settings."""
        self.settings.beginGroup('mainwindow')
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('windowstate', self.saveState())
        dock_state = self.dock_area.saveState()
        # dock_state returned here is a python dictionary. Coundn't find a good
        # way to save dicts in QSettings, hence just using representation
        # of it.
        self.settings.setValue('dockstate', repr(dock_state))
        self.settings.endGroup()

    def closeEvent(self, event):
        self.saveSettings()
        self.image_browser.saveSettings()
        super(MainWindow, self).closeEvent(event)

    def setWindowTitle(self, newTitle=''):
        """Prepend IP-BEC to all window titles."""
        title = 'IP-BEC: ' + newTitle
        super(MainWindow, self).setWindowTitle(title)
