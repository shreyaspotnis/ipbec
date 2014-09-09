from PyQt4 import uic
import os

curr_dir = os.path.dirname(os.path.abspath(__file__))
ui_file = os.path.join(curr_dir, "sterngerlach.ui")

Ui_PluginDialog, QDialog = uic.loadUiType(ui_file)


class PluginDialog(QDialog, Ui_PluginDialog):
    """Handles the plugin dialogbox."""

    name = "Stern Gerlach"

    def __init__(self, settings, data_dict):
        super(PluginDialog, self).__init__()
        self.settings = settings

        self.setupUi(self)


