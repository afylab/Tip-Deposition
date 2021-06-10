'''
Window to display the current status of the equipment
'''

from Interfaces.Base_Status_Window import Ui_StatusWindow
from customwidgets import VarEntry, CustomViewBox

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QComboBox

from datetime import datetime
from os.path import join

# Unfortuantly pyqtgraph prints lots of warnings, becuase it's logarthmic plotting
# Ignore the warnings here.
import warnings
warnings.filterwarnings("ignore")

class Status_Window(Ui_StatusWindow):
    '''
    The window to display information about the system.

    Args:
        widget : the QWidget that is the base for this window
        gui : The main GUI this window adds onto, usually the process main window.
        equipment : The Equipment handler object
    '''
    def __init__(self, widget, gui, equipment):
        super(Status_Window, self).__init__()

        # Connect the equipment handler and all it's signals
        self.equip = equipment
        self.equip.guiTrackedVarSignal.connect(self.trackedVariableSlot)
        self.equip.updateTrackedVarSignal.connect(self.updateTrackedVarSlot)

        self.widget = widget
        self.gui = gui

        # Switch to using white background and black foreground
        # Call before setupUi
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        self.setupUi(self.widget)

        self.t0 = datetime.now()

        self.trackedVarsWidgets = dict()
        self.trackedVarsData = dict()
        self.trackedrow = 0

        # Setup plots
        self.extraWindows = []
        self.plots = [self.plot0, self.plot1, self.plot2] # Add more plots later maybe
        self.plottedVars = dict()
        self.pgPen = pg.mkPen(41, 128, 185)
        for plot in self.plots:
            self.setupPlot(plot)

        # Open the default values
        self.defaultVar = "Pressure" # We always want to plot pressure
    #

    def setupUi(self, widget):
        super(Status_Window, self).setupUi(widget)
        widget.setWindowTitle("Tip Status Window")
        widget.setGUIRef(self.gui) # IMPORTANT, to make window closing work due to convoluted nature of Qt Designer classes

        # Initlize the plotting widgets
        self.plot0 = pg.PlotWidget(self.defaultPlotFrame, viewBox=CustomViewBox())
        self.plot0.setGeometry(QtCore.QRect(0, 0, 550, 400))
        self.plot0.setObjectName("plot0")

        self.plot1 = pg.PlotWidget(self.plotFrame, viewBox=CustomViewBox())
        self.plot1.setGeometry(QtCore.QRect(0, 0, 550, 400))
        self.plot1.setObjectName("plot1")

        self.plot1comboBox = QComboBox(self.plotFrame)
        self.plot1comboBox.setGeometry(QtCore.QRect(450, 0, 100, 20))
        self.plot1comboBox.setObjectName("plot1comboBox")
        self.plot1comboBox.currentTextChanged.connect(lambda s: self.startPlotting(self.plot1, s))

        self.plot2 = pg.PlotWidget(self.plotFrame, viewBox=CustomViewBox())
        self.plot2.setGeometry(QtCore.QRect(550, 0, 550, 400))
        self.plot2.setObjectName("plot2")

        self.plot2comboBox = QComboBox(self.plotFrame)
        self.plot2comboBox.setGeometry(QtCore.QRect(1000, 0, 100, 20))
        self.plot2comboBox.setObjectName("plot2comboBox")
        self.plot2comboBox.currentTextChanged.connect(lambda s: self.startPlotting(self.plot2, s))

        self.widget.setWindowIcon(QIcon(join('Interfaces','images','squid_tip.png')))
    #

    def setupPlot(self, widget):
        for k in list(self.plottedVars.keys()): # The plot is already in use, overwrite it
            if self.plottedVars[k][0] == widget:
                return
        widget.setTitle("Choose Data For Display")
        widget.setLabel('left',"")
        widget.setLabel('bottom',"time (s)")
        widget.setXRange(0,1)
        widget.setYRange(0,1)
    #

    def trackedVariableSlot(self, create, name, units):
        '''
        Add or remove a tracked variable to the GUI. If a varaible is already

        Args:
            create (bool) : If True will add it, if False will remove.
            name (str) : The name of the tracked varaible, will display.
            units (str) : The units of the tracked varaible, will display. Ignored if deleting.
        '''
        if create:
            # Create the widget
            widget = VarEntry(self.variablesFrame, name, units)
            widget.move(10, 32*self.trackedrow)
            self.trackedVarsWidgets[name] = widget
            self.trackedrow += 1

            # Create the data buffer
            newdata = np.zeros((1,2))
            newdata[0,0] = (datetime.now() - self.t0).total_seconds()
            newdata[0,1] = float(self.equip.info[name])
            self.trackedVarsData[name] = newdata

            for plot in [self.plot1comboBox, self.plot2comboBox]:
                if name != self.defaultVar:
                    plot.addItem(name)

            self.plotIfAvailible(name)
        else:
            if name in self.trackedVarsWidgets and (name != self.defaultVar):
                if name != self.defaultVar:
                    widget = self.trackedVarsWidgets.pop(name)
                    widget.deleteLater()
                    self.trackedVarsData.pop(name)
                for cb in [self.plot1comboBox, self.plot2comboBox]:
                    cb.removeItem(cb.findText(name))
    #

    def updateTrackedVarSlot(self, name):
        '''
        Update the value of a tracked variable. If a variable does not exist, command is
        ignored. Value of varaible is taken from the EquipmentHandler.info[name]

        Args:
            name (str) : The name of the tracked varaible to update.
        '''
        try:
            if name in self.trackedVarsWidgets:
                val = self.equip.info[name]
            self.trackedVarsWidgets[name].setValue(val)

            # Update the data
            t = (datetime.now() - self.t0).total_seconds()
            self.trackedVarsData[name] = np.append(self.trackedVarsData[name], np.array([t, val]).reshape(1,2), axis=0)

            if name in self.plottedVars:
                self.updatePlot(name)
        except KeyError:
            print("KeyError Could not update " + name)
    #

    def reset(self):
        '''
        Restart the status window, normally used when re-loading a recipe.
        Zeros out the data buffers, removing old data.
        '''
        self.t0 = datetime.now()

        # Clear the plots
        if self.plottedVars:
            for k in list(self.plottedVars.keys()):
                plot = self.plottedVars.pop(k)
                plot[1].clear()
        for plot in self.plots:
            self.setupPlot(plot)

        if self.trackedVarsWidgets: # Dicitonaries evaluate to False if they are empty, True otherwise
            for k in list(self.trackedVarsWidgets.keys()):
                saveix = 0
                if k != self.defaultVar:
                    widget = self.trackedVarsWidgets.pop(k)
                    widget.deleteLater()
                    self.trackedVarsData.pop(k)
                    for cb in [self.plot1comboBox, self.plot2comboBox]:
                        cb.removeItem(cb.findText(k))
                else:
                    saveix += 1
                    self.trackedVarsData.pop(k)
                    newdata = np.zeros((1,2))
                    newdata[0,0] = (datetime.now() - self.t0).total_seconds()
                    newdata[0,1] = float(self.equip.info[k])
                    self.trackedVarsData[k] = newdata
                    self.plotIfAvailible(k)
            self.trackedrow = saveix
    #

    def plotIfAvailible(self, variable):
        '''
        Plots a variable to a new plot, if one it availible.

        Args:
            varaible (str) : The tracked varaible to plot
            start (bool) : If True will start plotting, if False will stop.
            logy (bool) : If True will make the y-axis logarithmic
        '''
        if variable == self.defaultVar:
            self.startPlotting(self.plot0, variable)
        for plot in [self.plot1, self.plot2]:
            inuse = False
            for k in list(self.plottedVars.keys()):
                if self.plottedVars[k][0] == plot:
                    inuse = True
            if not inuse:
                self.startPlotting(plot, variable)
                return
    #

    def startPlotting(self, plotWidget, variable):
        '''
        Starts plotting to a plot widget and creates and entry for it in self.plottedVars
        Will overwrite a plot if it is already in use.

        Args:
            plot : The PlotWidget to plot onto.
            variable (str) : The name of the tracked variable in self.equip.info to plot
        '''
        if variable in self.plottedVars: # If it's already plotted do nothing.
            return
        if variable not in self.equip.info:
            raise ValueError("Cannot plot, variable " + str(variable) + " not tracked")
        try:
            float(self.equip.info[variable])
        except:
            raise ValueError("Cannot plot, variable " + str(variable) + " is not numeric.")
        #

        inuse = None # The plot is already in use, overwrite it
        for k in list(self.plottedVars.keys()):
            if self.plottedVars[k][0] == plotWidget:
                inuse = k
        if inuse is not None:
            self.plottedVars.pop(inuse)
        plotWidget.clear()
        #
        data = self.trackedVarsData[variable]
        curve = plotWidget.plot(data[:,0], data[:,1], pen=self.pgPen)
        if variable == self.defaultVar:
            plotWidget.setLogMode(0, 1)
        plotWidget.enableAutoRange()
        plotWidget.setTitle(variable)
        self.plottedVars[variable] = [plotWidget, curve]
    #

    def updatePlot(self, variable):
        '''
        Updates a plot with new data.

        Args:
            variable (str) : The name of the tracked variable to update. Must be a key of
            self.plottedVars
        '''
        if variable not in self.plottedVars:
            raise ValueError("Cannot update plot, variable " + str(variable) + " not being plotted")
        widget, curve = self.plottedVars[variable]
        data = self.trackedVarsData[variable]
        curve.setData(x=data[:,0], y=data[:,1]) # Update the plot
    #
#
