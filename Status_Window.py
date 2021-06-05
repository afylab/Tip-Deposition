'''
Window to display the current status of the equipment
'''

from Interfaces.Base_Status_Window import Ui_StatusWindow
from customwidgets import VarEntry, BaseStatusWidget, CustomViewBox

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore

from PyQt5.QtGui import QIcon

from datetime import datetime
from os.path import join

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
        self.equip.plotVariableSignal.connect(self.plottingSlot)

        self.widget = widget
        self.gui = gui

        # Switch to using white background and black foreground
        # Call before setupUi
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        self.setupUi(self.widget)

        self.t0 = datetime.now()

        self.trackedVarsWidgets = dict()
        self.trackedrow = 0

        # Setup plots
        self.extraWindows = []
        self.plots = [self.plot1, self.plot2] # Add more plots later maybe
        self.plottedVars = dict()
        self.pgPen = pg.mkPen(41, 128, 185)
        for plot in self.plots:
            self.setupPlot(plot)

        # Open the default values
        self.alwaysPlot = ["Pressure"] # If a varaible is in this it's always plotted and never deleted
        # Generlly pressure will get added when the equipment handler starts up.
    #

    def setupUi(self, widget):
        super(Status_Window, self).setupUi(widget)
        widget.setWindowTitle("Tip Status Window")
        widget.setGUIRef(self.gui) # IMPORTANT, to make window closing work due to convoluted nature of Qt Designer classes

        # Initlize the plotting widgets
        self.plot1 = pg.PlotWidget(self.plotFrame, viewBox=CustomViewBox())
        self.plot1.setGeometry(QtCore.QRect(0, 0, 550, 400))
        self.plot1.setObjectName("plot1")
        self.plot2 = pg.PlotWidget(self.plotFrame, viewBox=CustomViewBox())
        self.plot2.setGeometry(QtCore.QRect(0, 400, 550, 400))
        self.plot2.setObjectName("plot2")

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

    def reset(self):
        '''
        Restart the status window, normally used when re-loading a recipe
        '''
        if self.trackedVarsWidgets: # Dicitonaries evaluate to False if they are empty, True otherwise
            for k in list(self.trackedVarsWidgets.keys()):
                saveix = 0
                if k not in self.alwaysPlot:
                    widget = self.trackedVarsWidgets.pop(k)
                    widget.deleteLater()
                else:
                    saveix += 1
            self.trackedrow = saveix
        self.t0 = datetime.now()
        if self.plottedVars:
            for k in list(self.plottedVars.keys()):
                if k in self.alwaysPlot:
                    self.zeroPlot(k)
                else:
                    plot = self.plottedVars.pop(k)
                    plot[1].clear()
        for plot in self.plots:
            self.setupPlot(plot)
        #self.default()
    #

    def plottingSlot(self, variable, start, logy):
        '''
        Plots a variable to an availible plot, or makes a new one if there is no
        availible plot.

        Args:
            varaible (str) : The tracked varaible to plot
            start (bool) : If True will start plotting, if False will stop.
            logy (bool) : If True will make the y-axis logarithmic
        '''
        if start:
            for plot in self.plots:
                inuse = False
                for k in list(self.plottedVars.keys()):
                    if self.plottedVars[k][0] == plot:
                        inuse = True
                if not inuse:
                    self.startPlotting(plot, variable, logy=logy)
                    return
            # If there is not availible plot, make one
            base = BaseStatusWidget()
            self.extraWindows.append(base)
            newplot = pg.PlotWidget(base, viewBox=CustomViewBox())
            newplot.setGeometry(QtCore.QRect(0, 0, 550, 400))
            self.plots.append(newplot)
            self.startPlotting(newplot, variable, logy=logy)
            base.show()
        else:
            self.stopPlotting(variable)
    #

    def startPlotting(self, plotWidget, variable, logy=False):
        '''
        Starts plotting to a plot widget and creates and entry for it in self.plottedVars
        Will overwrite a plot if it is already in use. If a varaible is already being
        plotted will do nothing.

        Args:
            plot : The PlotWidget to plot onto.
            variable (str) : The name of the tracked variable in self.equip.info to plot
            logy (bool) : If True will make the y-axis logarithmic
        '''
        if variable in self.plottedVars: # If it's already plotted do nothing.
            return
        if variable not in self.equip.info:
            raise ValueError("Cannot plot, variable " + str(variable) + " not tracked")
        try:
            val = float(self.equip.info[variable])
        except:
            raise ValueError("Cannot plot, variable " + str(variable) + " is not numeric.")
        #

        inuse = None # The plot is already in use, overwrite it
        for k in list(self.plottedVars.keys()):
            if self.plottedVars[k][0] == plotWidget:
                inuse = k
        if inuse is not None:
            self.stopPlotting(inuse)
        plotWidget.clear()
        #
        data = np.zeros((1,2))
        data[0,0] = (datetime.now() - self.t0).total_seconds()
        data[0,1] = val
        curve = plotWidget.plot(data[:,0], data[:,1], pen=self.pgPen)
        if logy:
            plotWidget.setLogMode(0, 1)
        else:
            plotWidget.setLogMode(None, None)
        plotWidget.enableAutoRange()
        plotWidget.setTitle(variable)
        self.plottedVars[variable] = [plotWidget, curve, data]
    #

    def stopPlotting(self, variable):
        '''
        Stops plotting a variable, does not clear the plot. If a variable is not being
        plotted nothing happens. Certain variables are always plotted, thus this is ignored
        '''
        if variable in self.alwaysPlot:
            return
        if variable in self.plottedVars:
            self.plottedVars.pop(variable)
    #

    def updatePlot(self, variable):
        '''
        Updates a plotled with new data.

        DEV NOTE: For now making axes time since the plot was started, may need to do some
        more sophisticated timing later, especially when recording the data.

        Args:
            variable (str) : The name of the tracked variable to update. Must be a key of
            self.plottedVars
        '''
        if variable not in self.plottedVars:
            raise ValueError("Cannot update plot, variable " + str(variable) + " not being plotted")
        widget, curve, data = self.plottedVars[variable]
        t = (datetime.now() - self.t0).total_seconds()
        data = np.append(data, np.array([t, self.equip.info[variable]]).reshape(1,2), axis=0)
        curve.setData(x=data[:,0], y=data[:,1]) # Update the plot
        self.plottedVars[variable][2] = data # Save the data
    #

    def zeroPlot(self, variable):
        """
        Resets the range of the plot, removing old data.
        """
        plotWidget, curve, data = self.plottedVars[variable]
        newdata = np.zeros((1,2))
        newdata[0,0] = (datetime.now() - self.t0).total_seconds()
        newdata[0,1] = float(self.equip.info[variable])
        curve.clear()
        curve = plotWidget.plot(newdata[:,0], newdata[:,1], pen=self.pgPen)
        plotWidget.enableAutoRange()
        self.plottedVars[variable] = [plotWidget, curve, newdata]
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
            widget = VarEntry(self.variablesFrame, name, units)
            widget.move(10, 32*self.trackedrow)
            self.trackedVarsWidgets[name] = widget
            self.trackedrow += 1
        else:
            if name in self.trackedVarsWidgets and (name not in self.alwaysPlot):
                if name not in self.alwaysPlot:
                    widget = self.trackedVarsWidgets.pop(name)
                    widget.deleteLater()
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
            if name in self.plottedVars:
                self.updatePlot(name)
        except KeyError:
            print("KeyError Could not update " + name)
    #
#
