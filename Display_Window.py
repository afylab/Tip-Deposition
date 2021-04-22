from Interfaces.Base_Display_Window import Ui_DisplayWindow
from customwidgets import CustomViewBox, VarEntry
from exceptions import LogFileFormatError

#import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFileDialog
from PyQt5 import QtGui

from os.path import join, exists
from os import makedirs

import labrad
import numpy as np

def retrievedatafromvault(vaultdir, squidname, host='localhost', password='pass'):
    '''
    A tool to retrieve files from a LabRAD datavault

    Args:
        vaultdir (str) : The sub directory of the vault to find the files in (neglecting the .dir extension)
        squidname (str) : The name of the squid.
        host (str) : The host for the labrad connection, localhost by default.
        password (str) : The password for the labrad connection, localhost password by default.

    Returns:
        A dictionary of variables and their data, where the keys are varaible names and the
        values are numpy arrays of data.
    '''
    dv = labrad.connect('localhost', password='pass').data_vault
    for dir in vaultdir.split('\\'):
        dv.cd(dir)
    rt, fls = dv.dir()
    ret = dict()
    for fl in fls:
        s = fl.split(' - ')
        if len(s) > 1 and s[1] == squidname:
            dv.open(fl)
            ret[s[2]] = np.array(dv.get())
    return ret
#

class Display_Window(Ui_DisplayWindow):
    '''
    The window to display information about the system.

    Args:
        parent : the parent widget of the window
        version (str) : The recipe version string to load data from (same as database notation)
        squidname (str) : The name of the SQUID to load
        database (str) : The root tip database, same as location where parameters are saved
        autosave (bool) : If True will automatically save the screenshot when loaded
    '''
    def __init__(self, parent, version, squidname, database='..\database', autosave=False):
        super().__init__()
        self.parent = parent
        self.version = version
        self.squidname = squidname
        self.squiddatabase = database
        self.home_dir = join(database, version+' Data')
        if not exists(self.home_dir):
            makedirs(self.home_dir)
        self.autosave = autosave
        self.pgPen = pg.mkPen(41, 128, 185)
        self.floatpercision = 3

        self.setupUi(self.parent)
        self.loaddata()
        self.parent.show()
    #

    def setupUi(self, widget):
        super().setupUi(widget)
        widget.setWindowTitle("Tip Status Window")

        # Initlize the plotting widgets
        self.plot1 = pg.PlotWidget(self.plotFrame, viewBox=CustomViewBox())
        self.plot1.setGeometry(QtCore.QRect(0, 0, 550, 400))
        self.plot1.setObjectName("plot1")
        self.plot2 = pg.PlotWidget(self.plotFrame, viewBox=CustomViewBox())
        self.plot2.setGeometry(QtCore.QRect(0, 400, 550, 400))

        self.notesBrowser.setReadOnly(False)

        # Bind Buttons
        self.saveButton.clicked.connect(self.saveCallback)

        widget.setWindowIcon(QIcon(join('Interfaces','images','squid_pattern.png')))
    #

    def loaddata(self):
        data = retrievedatafromvault(join('Tip Deposition Database',self.version), self.squidname)
        ix = 0
        for k in list(data.keys()):
            if ix == 0:
                self._loadplot(self.plot1, k, data[k])
            elif ix == 1:
                self._loadplot(self.plot2, k, data[k])
            else:
                print("Warning " + str(k) + " not plotted. Out of useable plots.")
            ix += 1
        #

        if exists(join(self.home_dir, self.squidname+' - Notes.txt')):
            with open(join(self.home_dir, self.squidname+' - Notes.txt'),'r') as fl:
                text = fl.read()
            self.notesBrowser.setPlainText(text)
            self.notesBrowser.moveCursor(QtGui.QTextCursor.End)

        params = self._loadparams()
        self.varsWidgets = dict()
        row = 0
        for name in list(params.keys()):
            widget = VarEntry(self.parametersFrame, name, labelwidth=250)
            widget.setValue(params[name])
            widget.move(10, 30*row)
            self.varsWidgets[name] = widget
            row += 1


        if self.autosave:
            svfl = join(self.home_dir, self.squidname+'.png')
            if not exists(svfl):
                screenshot = self.parent.grab()
                screenshot.save(svfl)
    #

    def saveCallback(self):
        filename = QFileDialog.getSaveFileName(self.parent, 'Save', join(self.home_dir, self.squidname+'.png'), "Images (*.png *.jpg)")
        if filename[0]:
            screenshot = self.parent.grab()
            screenshot.save(filename[0])

            text = self.notesBrowser.toPlainText()
            with open(join(self.home_dir, self.squidname+' - Notes.txt'),'w') as fl:
                fl.write(text)
                fl.flush()
            #
    #

    def _loadplot(self, plotWidget, variable, data):
        plotWidget.setLabel('left',"")
        plotWidget.setLabel('bottom',"time (s)")
        plotWidget.plot(data[:,0], data[:,1], pen=self.pgPen)
        plotWidget.setTitle(variable)
    #

    def _loadparams(self):
        '''
        Load parameters of a previous run from the log.

        Returns:
            Returns a dictionary of strings 'name':'value' where 'name' is the name from the first row
            and 'value' is a string read from the row. If it is a new log returns None.

        Raises:
            LogFileFormatError is the log file is incorrectly formatted.
        '''
        flpath = join(self.squiddatabase, self.version+'_params'+'.csv')
        with open(flpath, 'r') as reader:
            lines = reader.readlines()
        #
        if len(lines) < 2:
            raise LogFileFormatError("Improperly Formatted Log File")

        firstline = lines[0].split(',')
        firstline[len(firstline)-1] = firstline[len(firstline)-1].rstrip()

        ix = -1
        for i in range(1,len(lines)):
            ln = lines[i].split(',')
            if ln[1] == self.squidname:
                ix = i
                break
        if ix == -1: # Default to last line if the
            ix = len(lines) - 1
            print("SQUID name " + self.squidname + "not found, loading paramters from last deposition.")

        params = lines[ix].split(',')
        if len(params) != len(firstline) or len(params) < 1:
            raise LogFileFormatError("Improperly Formatted Log File")
        ret = dict()
        for i in range(1, len(params)): # Does not include first entry, which is the date
            ret[firstline[i]] = params[i].rstrip()
        return ret
    #
#
