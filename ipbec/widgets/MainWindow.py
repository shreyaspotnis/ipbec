from PyQt4 import uic
from pyqtgraph.dockarea import DockArea, Dock
from PyQt4.QtGui import QScrollArea, QAction
from PyQt4.QtCore import QSignalMapper, QString, SIGNAL, SLOT
import os

from ipbec.widgets import ImageView, ImageBrowser, Fitter, RoiEditor, Plot1d
from ipbec.widgets import Analyzer
from ipbec.plugins import plugin_list

main_package_dir = os.path.join(os.path.dirname(__file__), os.pardir)
ui_filename = os.path.join(main_package_dir, "ui/MainWindow.ui")
Ui_MainWindow, QMainWindow = uic.loadUiType(ui_filename)


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
        # self.image_browser.populateAndEmitImageInfo()
        self.image_browser.initialEmit()
        self.roi_editor_h.initialEmit()
        self.roi_editor_v.initialEmit()
        self.roi_editor_int.initialEmit()
        self.roi_editor_err.initialEmit()

        self.loadPlugins()

    def loadPlugins(self):
        """Looks for all plugins and creates menu entries, signals and
           slots for them."""
        self.pluginSignalMapper = QSignalMapper(self)
        for p in plugin_list:
            click_action = QAction(p.name, self)
            self.menuPlugins.addAction(click_action)
            self.connect(click_action, SIGNAL("triggered()"),
                         self.pluginSignalMapper, SLOT("map()"))
            self.pluginSignalMapper.setMapping(click_action, QString(p.name))
        self.connect(self.pluginSignalMapper,
                     SIGNAL("mapped(const QString &)"),
                     self.image_browser.handlePluginClicked)


    def createDocks(self):
        """Create all dock widgets and add them to DockArea."""
        self.image_view = ImageView(self.settings, self)
        self.image_browser = ImageBrowser(self.settings, self)
        self.fitter = Fitter(self.settings, self)

        self.roi_editor_h = RoiEditor(self.settings,
                                      self.image_view, self, name='ROIH',
                                      pen=(1, 9), axis=1)
        self.roi_editor_v = RoiEditor(self.settings,
                                      self.image_view, self, name='ROIV',
                                      pen=(1, 1), axis=0)
        self.roi_editor_int = RoiEditor(self.settings,
                                        self.image_view, self, name='ROI Int',
                                        pen=(1, 2), axis=1)
        self.roi_editor_err = RoiEditor(self.settings,
                                        self.image_view, self, name='ROI Err',
                                        pen=(1, 3), axis=1)
        self.roi_plot_h = Plot1d(parent=self, title='ROI H')
        self.roi_plot_v = Plot1d(parent=self, title='ROI V')

        self.analyzer = Analyzer(self.settings, parent=self)

        # Create docks for all widgets
        self.dock_image_view = Dock('Image View', widget=self.image_view)
        self.dock_image_browser = Dock('Image Browser',
                                       widget=self.image_browser)
        self.dock_fitter = Dock('Fitter', widget=self.fitter)
        self.dock_roi_h = Dock('ROIH', widget=self.roi_editor_h)
        self.dock_roi_v = Dock('ROIV', widget=self.roi_editor_v)
        self.dock_roi_int = Dock('ROI Int', widget=self.roi_editor_int)
        self.dock_roi_err = Dock('ROI Err', widget=self.roi_editor_err)

        self.dock_roi_plot_h = Dock('ROIH Plot', widget=self.roi_plot_h)
        self.dock_roi_plot_v = Dock('ROIV Plot', widget=self.roi_plot_v)
        self.dock_analyzer = Dock('Analyze', widget=self.analyzer)

        self.dock_area.addDock(self.dock_image_view, position='top')
        self.dock_area.addDock(self.dock_image_browser, position='right',
                               relativeTo=self.dock_image_view)
        self.dock_area.addDock(self.dock_fitter, position='left',
                               relativeTo=self.dock_image_view)
        self.dock_area.addDock(self.dock_roi_h, position='bottom',
                               relativeTo=self.dock_fitter)
        self.dock_area.addDock(self.dock_roi_v, position='below',
                               relativeTo=self.dock_roi_h)
        self.dock_area.addDock(self.dock_roi_int, position='below',
                               relativeTo=self.dock_roi_v)
        self.dock_area.addDock(self.dock_roi_err, position='below',
                               relativeTo=self.dock_roi_int)
        self.dock_area.addDock(self.dock_roi_plot_h, position='below',
                               relativeTo=self.dock_image_view)
        self.dock_area.addDock(self.dock_roi_plot_v, position='right',
                               relativeTo=self.dock_roi_plot_h)
        self.dock_area.addDock(self.dock_analyzer, position='top',
                               relativeTo=self.dock_image_browser)

    def initAfterCreatingDockWidgets(self):
        self.setWindowTitle(self.image_browser.current_directory)

    def connectSignalsToSlots(self):
        self.actionOpen_Directory.triggered.connect(self.image_browser.handleOpenDirectoryAction)
        self.actionDark_File.triggered.connect(self.image_browser.handleDarkFileAction)
        self.actionRefresh.triggered.connect(self.image_browser.handleRefreshAction)
        self.actionSave.triggered.connect(self.image_browser.handleSaveAnalysis)

        self.image_browser.windowTitleChanged.connect(self.setWindowTitle)
        # self.image_browser.imageChanged.connect(self.image_view.handleImageChanged)
        self.image_browser.imageChanged.connect(self.fitter.handleImageChanged)
        self.image_browser.imageChanged.connect(self.analyzer.handleImageChanged)

        self.roi_editor_int.roiChanged.connect(self.image_browser.handleRoiChanged)
        self.roi_editor_err.roiChanged.connect(self.image_browser.handleROIErrChanged)
        self.roi_editor_h.roiChanged.connect(self.image_browser.handleROIHChanged)
        self.roi_editor_v.roiChanged.connect(self.image_browser.handleROIVChanged)

        self.roi_editor_h.roiChanged.connect(self.fitter.handleROIHChanged)
        self.roi_editor_h.roiChanged.connect(self.analyzer.handleROIHChanged)
        self.roi_editor_v.roiChanged.connect(self.fitter.handleROIVChanged)
        self.roi_editor_v.roiChanged.connect(self.analyzer.handleROIVChanged)
        self.roi_editor_int.roiChanged.connect(self.fitter.handleROIIntChanged)
        self.roi_editor_int.roiChanged.connect(self.analyzer.handleROIIntChanged)
        self.roi_editor_err.roiChanged.connect(self.fitter.handleROIErrChanged)
        self.roi_editor_err.roiChanged.connect(self.analyzer.handleROIErrChanged)

        self.image_view.doubleClicked.connect(self.roi_editor_h.centerROI)
        self.image_view.doubleClicked.connect(self.roi_editor_v.centerROI)

        self.fitter.imageChanged.connect(self.image_view.handleImageChanged)
        self.fitter.horDataChanged.connect(self.roi_plot_h.handleDataChanged)
        self.fitter.verDataChanged.connect(self.roi_plot_v.handleDataChanged)
        self.fitter.doneFitting.connect(self.analyzer.handleDoneFitting)

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
        self.roi_editor_int.saveSettings()
        self.roi_editor_err.saveSettings()
        self.roi_editor_v.saveSettings()
        self.roi_editor_h.saveSettings()
        self.analyzer.saveSettings()
        super(MainWindow, self).closeEvent(event)

    def setWindowTitle(self, newTitle=''):
        """Prepend IP-BEC to all window titles."""
        title = 'IP-BEC: ' + newTitle
        super(MainWindow, self).setWindowTitle(title)
