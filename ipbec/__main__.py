#!/usr/bin/env python

import sys
import os
from PyQt4 import QtGui, QtCore
from ipbec.widgets import MainWindow
from sys import platform as _platform

main_dir = os.path.dirname(os.path.abspath(__file__))
path_to_icon = os.path.join(main_dir, 'icon.png')


def main():
    # see if we can write to main_dir
    if os.access(main_dir, os.W_OK):
        # if yes, then put all settings in an ini file there
        path_to_settings = os.path.join(main_dir, 'settings.ini')
        settings = QtCore.QSettings(path_to_settings, QtCore.QSettings.IniFormat)
    else:
        # else use Qt settings system
        settings = QtCore.QSettings('IPBEC', 'Shreyas Potnis')
    w = MainWindow(settings)
    w.setWindowIcon(QtGui.QIcon(path_to_icon))
    w.show()
    return app.exec_()

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    if _platform == "win32":
        import ctypes
        myappid = 'mycompany.myproduct.subproduct.version'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    app.setWindowIcon(QtGui.QIcon(path_to_icon))

    main()
    os._exit(0)
