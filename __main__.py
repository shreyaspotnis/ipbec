#!/usr/bin/env python

import sys
import os
from PyQt4 import QtGui, QtCore
from widgets import MainWindow


def main():
    main_dir = os.path.dirname(os.path.abspath(__file__))
    path_to_settings = os.path.join(main_dir, 'settings.ini')
    settings = QtCore.QSettings(path_to_settings, QtCore.QSettings.IniFormat)
    w = MainWindow(settings)
    w.show()
    return app.exec_()

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    main()
    os._exit(0)
