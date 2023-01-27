import sys
from PyQt5 import QtCore, QtWidgets, uic
import labrad
from equipmenthandler import EquipmentHandler
import pyqtgraph as pg
from pyqtgraph import PlotWidget, plot
import numpy as np
from customwidgets import VarEntry, CustomViewBox
from twisted.internet.defer import inlineCallbacks

class Ui_MainWindow(object):

    def __init__(self):
        super(Ui_MainWindow, self).__init__()
        print('init')
        self.equip = EquipmentHandler()
        self.equip.errorSignal.connect(self.equipErrorSlot)
        self.equip.serverNotFoundSignal.connect(self.serverErrorSlot)
        self.equip.start()
        self.connect()

    def setupUi(self, MainWindow):

        print('setupUI')
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.Voltage_start = QtWidgets.QLineEdit(self.centralwidget, placeholderText='-0.1')
        self.Voltage_start.setGeometry(QtCore.QRect(30, 40, 71, 41))
        self.Voltage_start.setObjectName("Voltage_start")
        self.Voltage_end = QtWidgets.QLineEdit(self.centralwidget, placeholderText='0.1')
        self.Voltage_end.setGeometry(QtCore.QRect(130, 40, 71, 41))
        self.Voltage_end.setObjectName("Voltage_end")
        self.AC_excitation = QtWidgets.QLineEdit(self.centralwidget, placeholderText='0.001')
        self.AC_excitation.setGeometry(QtCore.QRect(330, 40, 71, 41))
        self.AC_excitation.setObjectName("AC_excitation")
        self.Steps = QtWidgets.QLineEdit(self.centralwidget, placeholderText='10')
        self.Steps.setGeometry(QtCore.QRect(540, 40, 71, 41))
        self.Steps.setObjectName("Steps")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(60, 10, 131, 20))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(110, 50, 21, 20))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(290, 20, 131, 20))
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(self.centralwidget)
        self.label_4.setGeometry(QtCore.QRect(510, 20, 131, 20))
        self.label_4.setObjectName("label_4")
        self.Start_sweep = QtWidgets.QPushButton(self.centralwidget)
        self.Start_sweep.setGeometry(QtCore.QRect(680, 20, 91, 61))
        self.Start_sweep.setObjectName("Start_sweep")
        self.Start_sweep.clicked.connect(self.sweep_IV)
        self.PlotFrame = QtWidgets.QFrame(self.centralwidget)
        self.PlotFrame.setGeometry(QtCore.QRect(30, 100, 800, 500))
        # self.PlotFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        # self.PlotFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        # self.PlotFrame.setObjectName("frame")
        self.graphWidget = pg.PlotWidget(self.PlotFrame)
        self.graphWidget.setGeometry(QtCore.QRect(0, 0, 700, 400))
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.label.setText(_translate("MainWindow", "<html><head/><body><p align=\"center\"><span style=\" font-size:12pt;\">Voltage range, V</span></p></body></html>"))
        self.label_2.setText(_translate("MainWindow", "<html><head/><body><p align=\"center\">to</p></body></html>"))
        self.label_3.setText(_translate("MainWindow", "<html><head/><body><p align=\"center\"><span style=\" font-size:12pt;\">AC excitation, V</span></p></body></html>"))
        self.label_4.setText(_translate("MainWindow", "<html><head/><body><p align=\"center\"><span style=\" font-size:12pt;\">Steps</span></p></body></html>"))
        self.Start_sweep.setText(_translate("MainWindow", "Sweep"))

    @inlineCallbacks
    def sweep_IV(self, c):
        try:
            print(self.Voltage_start.text())
            Voltage_start = float(self.Voltage_start.text())
            Voltage_end = float(self.Voltage_end.text())
            AC_excitation = float(self.AC_excitation.text())
            Steps = int(self.Steps.text())
        except:
            print('except')
            Voltage_start = -0.1
            Voltage_end = 0.1
            AC_excitation = 0.001
            Steps = 100
        # print('sweep')
        # print(self.Voltage_start.text(), ' ', self.Voltage_end.text(), ' ', self.AC_excitation.text(), ' ', self.Steps.text())
        voltages = np.linspace(Voltage_start, Voltage_end, Steps)
        print(voltages)
        ans = yield self.sr860.sine_offset(Voltage_start)
        print(ans)
        ans = yield self.sr860.sine_out_amplitude(AC_excitation)
        print(ans)
        data = []
        ramp_up_voltage = np.linspace(0, Voltage_start, 500)
        ramp_down_voltage = np.linspace(Voltage_end, 0, 500)

        for i in range(500):
            yield self.sr860.sine_offset(ramp_up_voltage[i])

        for i in range(Steps):
            print(voltages[i])
            yield self.sr860.sine_offset(voltages[i])
            x = yield self.sr860.x()
            data.append(x)
            
        for i in range(500):
            yield self.sr860.sine_offset(ramp_down_voltage[i])

        self.graphWidget.clear()
        self.graphWidget.plot(voltages, data)
        self.graphWidget.enableAutoRange()




    def equipErrorSlot(self):
        self.append_ins_warning("Equipment Error, see errorlog for details.")
        if hasattr(self, 'sequencer'):
            self.sequencer.abortSignal.emit()
            self.sequencer.record_error()
        else:
            print(format_exc())
        self.set_status('error')
    #

    def serverErrorSlot(self, txt):
        self.append_ins_warning("LabRAD Server Error: " + txt)
        self.append_ins_warning("Fix the servers and restart the program.")
        self.set_status('error')
        self.proceedButton.setEnabled(False)

    def connect(self):
        """
        Connects to the LabRAD servers and prepares the devices to listen to the commands

        return: None
        """

        self.cxn = labrad.connect('localhost', password='pass')
        print('connect')
        # Connectors to the valve/relay controller, the rvc pressure controller,
        # the stepper controller and the power supply controller.
        self.sr860 = self.cxn.sr860()
        ans = self.sr860.select_device()
        print(ans)

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
