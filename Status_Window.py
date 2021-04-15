'''
Window to display the current status of the equipment
'''

from Interfaces.Base_Status_Window import Ui_StatusWindow
from customwidgets import VarEntry, BaseStatusWidget

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore

from PyQt5.QtGui import QIcon

from datetime import datetime
from os.path import join

class CustomViewBox(pg.ViewBox):
    '''
    Viewbox that allows for selecting range, taken from PyQtGraphs documented examples
    '''
    def __init__(self, *args, **kwds):
        kwds['enableMenu'] = False
        pg.ViewBox.__init__(self, *args, **kwds)
        self.setMouseMode(self.RectMode)
    #

    ## reimplement right-click to zoom out
    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton:
            self.autoRange()
    #

    ## reimplement mouseDragEvent to disable continuous axis zoom
    def mouseDragEvent(self, ev, axis=None):
        if axis is not None and ev.button() == QtCore.Qt.RightButton:
            ev.ignore()
        else:
            pg.ViewBox.mouseDragEvent(self, ev, axis=axis)
    #
#

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

        self.trackedVarsWidgets = dict()
        self.trackedrow = 0

        self.floatpercision = 3

        # Setup plots
        self.extraWindows = []
        self.plots = [self.plot1, self.plot2] # Add more plots later maybe
        self.plottedVars = dict()
        for plot in self.plots:
            self.setupPlot(plot)

        # LabRAD Server Status Widget
        # self.labRADStatus = LabRAD_Server_Status()
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
        widget.setTitle("Choose Data For Display")
        widget.setLabel('left',"")
        widget.setLabel('bottom',"time (s)")
        widget.setXRange(0,1)
        widget.setYRange(0,1)
        self.pgPen = pg.mkPen(41, 128, 185)
    #

    def reset(self):
        '''
        Restart the status window, normally used when re-loading a recipe
        '''
        if self.trackedVarsWidgets: # Dicitonaries evaluate to False if they are empty, True otherwise
            for widget in self.trackedVarsWidgets: # Delete elements to avoid screwing up updating
                del widget
            self.trackedrow = 0
        if self.plottedVars:
            for k in list(self.plottedVars.keys()):
                plot = self.plottedVars.pop(k)
                plot[1].clear()
        for plot in self.plots:
            self.setupPlot(plot)
        if self.serverWidgets:
            del self.serverWidgets
            self.serverWidgets = dict()
    #

    def plottingSlot(self, variable, start):
        '''
        FOR NOW: Wrapper for starting the main plot,
        LATER add the ability to watch multiple plots.
        '''
        if start:
            for plot in self.plots:
                inuse = False
                for k in list(self.plottedVars.keys()):
                    if self.plottedVars[k][0] == plot:
                        inuse = True
                if not inuse:
                    self.startPlotting(plot, variable)
                    return
            # If there is not availible plot, make one
            base = BaseStatusWidget()
            self.extraWindows.append(base)
            newplot = pg.PlotWidget(base, viewBox=CustomViewBox())
            newplot.setGeometry(QtCore.QRect(0, 0, 550, 400))
            self.plots.append(newplot)
            self.startPlotting(newplot, variable)
            base.show()
        else:
            self.stopPlotting(variable)
    #

    def startPlotting(self, plotWidget, variable):
        '''
        Starts plotting to a plot widget and creates and entry for it in self.plottedVars
        Will overwrite a plot if it is already in use. If a varaible is already being plotted
        will do nothing.

        Args:
            plot : The PlotWidget to plot onto.
            variable (str) : The name of the tracked variable in self.equip.info to plot
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
        t0 = datetime.now()
        data = np.zeros((1,2))
        data[0,1] = val
        curve = plotWidget.plot(data[:,0], data[:,1], pen=self.pgPen)
        plotWidget.enableAutoRange()
        plotWidget.setTitle(variable)
        self.plottedVars[variable] = [plotWidget, curve, data, t0]
    #

    def stopPlotting(self, variable):
        '''
        Stops plotting a variable, does not clear the plot. If a variable is not being
        plotted nothing happens.
        '''
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
        widget, curve, data, t0 = self.plottedVars[variable]
        t = (datetime.now() - t0).total_seconds()
        data = np.append(data, np.array([t, self.equip.info[variable]]).reshape(1,2), axis=0)
        curve.setData(x=data[:,0], y=data[:,1]) # Update the plot
        self.plottedVars[variable][2] = data # Save the data
    #

    def trackedVariableSlot(self, name, create):
        '''
        Add or remove a tracked variable to the GUI.

        Args:
            name (str) : The name of the tracked varaible, will display.
            create (bool) : If True will add it, if False will remove.
        '''
        if create:
            widget = VarEntry(self.variablesFrame, name)
            widget.move(10, 32*self.trackedrow)
            self.trackedVarsWidgets[name] = widget
            self.trackedrow += 1
        else:
            # Do we need removal? Generally we define variables for the whole run?
            print("NEED TO IMPLEMENT REMOVAL")
    #

    def updateTrackedVarSlot(self, name):
        '''
        Update the value of a tracked variable. If a variable does not exist, command is
        ignored. Value of varaible is taken from the EquipmentHandler.info[name]

        Args:
            name (str) : The name of the tracked varaible to update.
        '''
        if name in self.trackedVarsWidgets:
            val = self.equip.info[name]
        if isinstance(val, float):
            s = str(round(val, self.floatpercision))
        else:
            s = str(val)
        self.trackedVarsWidgets[name].setValue(s)
        if name in self.plottedVars:
            self.updatePlot(name)
    #
#
