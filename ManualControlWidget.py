import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QLine, QPoint
from PyQt5.QtGui import QPolygon, QFont
from twisted.internet.defer import inlineCallbacks
import labrad
#import time
from os.path import join


class EvaporatorWidget(QtWidgets.QWidget):
    """
    Manual control widget pops up as a separate window from the main window.
    """

    def __init__(self, main, frame):
        super().__init__(frame)
        self.main = main  # The main interface
        self.setGeometry(0, 0, 500, 750)
        self.equip = dict()  #: dict attribute for all dynamic elements
        self.defineElements()
        # self.names = ['leak valve', 'gate valve', 'chamber valve', 'turbo valve', 'turbo pump', 'scroll pump',
        #               'evaporator power', 'effusion power', 'sputterer power',
        #               'evaporator shutter', 'effusion shutter']

        # EMERGENCY STOP DEPRACATED as it doesn't add much, in any real situation we would deal with
        # the valves/pumps in a better way and the turb would spin down automatically
        # it only adds the potential of someone clicking it when they are not supposed to
        # self.emergencystopbutton = QtWidgets.QPushButton('Emergency Stop', self)
        # self.emergencystopbutton.setToolTip('Valves will be closed and pumps will be turned off')
        # self.emergencystopbutton.setGeometry(225-50, 600, 150, 50)
        # self.emergencystopbutton.setStyleSheet("QPushButton{background-color : #cf0000;} "
        #                                        "QPushButton::pressed{background-color : #b90000;}")
        # self.emergencystopbutton.setFont(QFont('Times', 15))
        # self.emergencystopbutton.clicked.connect(self.emergencystop)

        self.refreshbutton = QtWidgets.QPushButton('Refresh', self)
        self.refreshbutton.setToolTip('Refresh the status of all components')
        self.refreshbutton.setGeometry(25, 25, 75, 25)
        self.refreshbutton.setStyleSheet("QPushButton{background-color : #ffffff;} "
                                         "QPushButton::pressed{background-color : #eeeeee;}")
        self.refreshbutton.setFont(QFont('Times', 12))
        self.refreshbutton.clicked.connect(self.refresh)

        self.setWindowIcon(QtGui.QIcon(join('Interfaces','images','squid_tip.png')))

        self.isConnected = False
        self.connect()
        self.show()
    #

    def defineElements(self):
        """
        Defines all the dynamic elements on the widget.

        returns: None
        """

        name = 'Heater'
        self.heaterbutton = QtWidgets.QPushButton('Heater', self)
        self.heaterbutton.setCheckable(True)
        self.heaterbutton.setToolTip('Toggle the heater')
        self.heaterbutton.setGeometry(280-50, 600, 75, 25)
        self.heaterbutton.setStyleSheet("QPushButton{background-color : #ffffff;} "
                                         "QPushButton::pressed{background-color : #eeeeee;}")
        self.heaterbutton.setFont(QFont('Times', 12))
        self.heaterbutton.clicked.connect(self.heater)

        # self.setpointinput = QtWidgets.QLineEdit(self)
        # self.equip[name].input.setReadOnly(False) # Until we implement a way for it to display the setpoint
        # self.equip[name].input.setPlaceholderText('Pressure')
        # self.equip[name].input.setGeometry(85-50, 310, 50, 20

        name = 'leak valve'
        self.equip[name] = Valve(self, 80-50, 358, 'hor', 'blue', name)
        self.equip[name].clicked.connect(self.equip[name].toggle)
        self.equip[name].label = QtWidgets.QLabel(name, self)
        self.equip[name].label.move(75-50, 290)
        self.equip[name].label.setStyleSheet('font-size: 16px; qproperty-alignment: AlignJustify;')
        self.equip[name].input = QtWidgets.QLineEdit(self)
        self.equip[name].input.setReadOnly(False) # Until we implement a way for it to display the setpoint
        self.equip[name].input.setPlaceholderText('Pressure')
        self.equip[name].input.setGeometry(85-50, 310, 50, 20)
        #self.equip[name].input.returnPressed.connect(self.helium_setpoint) # Comment until we implement a way for it to display the setpoint

        name = 'gate valve'
        self.equip[name] = Valve(self, 150-50, 460, 'ver', 'blue', name)
        self.equip[name].clicked.connect(self.equip[name].toggle)
        self.equip[name].label = QtWidgets.QLabel('gate\nvalve', self)
        self.equip[name].label.move(90-50, 470)
        self.equip[name].label.setStyleSheet('font-size: 16px; qproperty-alignment: AlignJustify;')

        name = 'chamber valve'
        self.equip[name] = Valve(self, 270-50, 430, 'hor', 'blue', name)
        self.equip[name].clicked.connect(self.equip[name].toggle)
        self.equip[name].label = QtWidgets.QLabel(name, self)
        self.equip[name].label.move(260-50, 450)
        self.equip[name].label.setStyleSheet('font-size: 16px; qproperty-alignment: AlignJustify;')

        name = 'turbo valve'
        self.equip[name] = Valve(self, 425-50, 460, 'ver', 'blue', name)
        self.equip[name].clicked.connect(self.equip[name].toggle)
        self.equip[name].label = QtWidgets.QLabel('turbo\nvalve', self)
        self.equip[name].label.move(450-50, 470)
        self.equip[name].label.setStyleSheet('font-size: 16px; qproperty-alignment: AlignJustify;')

        name = 'evaporator shutter'
        self.equip[name] = Shutter(self, 185-50, 190, 'ver', 'red', name)
        self.equip[name].clicked.connect(self.equip[name].toggle)
        self.equip[name].label = QtWidgets.QLabel('evaporator\nshutter', self)
        self.equip[name].label.move(100-50, 190)
        self.equip[name].label.setStyleSheet('font-size: 16px; qproperty-alignment: AlignJustify;')

        name = 'effusion shutter'
        self.equip[name] = Shutter(self, 350-50, 190, 'ver', QtGui.QColor(20, 30, 30), name)
        self.equip[name].clicked.connect(self.equip[name].toggle)
        self.equip[name].label = QtWidgets.QLabel('effusion\nshutter', self)
        self.equip[name].label.move(285-50, 190)
        self.equip[name].label.setStyleSheet('font-size: 16px; qproperty-alignment: AlignJustify;')

        name = 'scroll pump'
        self.equip[name] = Pump(self, 475-50, 410, name)
        self.equip[name].clicked.connect(self.equip[name].toggle)
        self.equip[name].label = QtWidgets.QLabel(name, self)
        self.equip[name].label.move(460-50, 390)
        self.equip[name].label.setStyleSheet('font-size: 16px; qproperty-alignment: AlignJustify;')

        name = 'turbo pump'
        self.equip[name] = Pump(self, 280-50, 530, name)
        self.equip[name].clicked.connect(self.equip[name].toggle)
        self.equip[name].label = QtWidgets.QLabel(name, self)
        self.equip[name].label.move(260-50, 510)
        self.equip[name].label.setStyleSheet('font-size: 16px; qproperty-alignment: AlignJustify;')

        name = 'evaporator power'
        self.equip[name] = Power(self, 165-50, 110, name)
        self.equip[name].label = QtWidgets.QLabel(name, self)
        self.equip[name].label.move(135-50, 80)
        self.equip[name].label.setStyleSheet('font-size: 16px; qproperty-alignment: AlignJustify;')

        name = 'effusion power'
        self.equip[name] = Power(self, 330-50, 110, name)
        self.equip[name].label = QtWidgets.QLabel(name, self)
        self.equip[name].label.move(295-50, 80)
        self.equip[name].label.setStyleSheet('font-size: 16px; qproperty-alignment: AlignJustify;')

        name = 'sputterer power'
        self.equip[name] = Power(self, 455-50, 110, name)
        self.equip[name].label = QtWidgets.QLabel(name, self)
        self.equip[name].label.move(435-50, 80)
        self.equip[name].label.setStyleSheet('font-size: 16px; qproperty-alignment: AlignJustify;')

        for key in self.equip.keys():
            self.equip[key].status = True

    def helium_setpoint(self):
        """
        Sets the pressure on the leak valve after QLineEdit is filled and Return button pressed.
        QMessage box pops up if the turbo pump is in danger.

        return: None
        """
        name = 'leak valve'
        if self.equip['turbo pump'].status and self.equip['gate valve'].status:
            msg = QtWidgets.QMessageBox()
            msg.setWindowTitle("Dangerous situation")
            msg.setText("Are you sure you want to open the leak valve while the turbo pump is active"
                        "and the gate valve is open?")

            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
            msg.setDefaultButton(QtWidgets.QMessageBox.Cancel)
            # msg.exec_()
            returnvalue = msg.exec()
            if returnvalue == QtWidgets.QMessageBox.Cancel:
                pass
                self.equip[name].input.clear()
            else:
                prs = self.equip[name].input.text()
                #prs = "{:.2E}".format(prs)
                self.equip[name].input.clear()
                print('helium pressure is ', prs)
                yield self.rvc.set_mode_prs()
                yield self.rvc.set_nom_prs(prs)

    # DEPRECATED, see comment in initilizer
    # def emergencystop(self):
    #     """
    #     Closes gate valve, chamber valve and turn off turbo pump. Turn on scroll pump and open turbo valve
    #     to have the access to the pump outlet.
    #
    #     return: None
    #     """
    #     self.main.abort()
    #
    #     self.vrs.gate_close()
    #     self.vrs.chamber_valve_close()
    #     self.vrs.turbo_valve_close()
    #     self.vrs.turbo_off()
    #     #self.vrs.scroll_off()
    #
    #     self.rvc.close_valve()
    #
    #     self.refresh()
    @inlineCallbacks
    def heater(self, c):
        """
        toggle the heater between off and high heat range.
        Active only if the leak valve is open.

        """
        if self.heaterbutton.isChecked():
            if self.equip['leak valve'].state:
                yield self.lakeshore.ramp(1, 0, 0)
                print('flag 1')
                yield self.lakeshore.read()
                cur_temp = yield self.lakeshore.read_temp()
                cur_temp = cur_temp.split(';')[0]
                print('Temperature is ', cur_temp)
                yield self.lakeshore.set_p(1, cur_temp)
                print('flag 2')
                yield self.lakeshore.set_heater_range(1,4)
                yield self.lakeshore.ramp(1, 1, 5)
                setp = yield self.lakeshore.read_p(1)
                print(setp)
                yield self.lakeshore.set_p(1, 300)
                print('flag 4')
            else:
                print('Leak valve is closed')
        else:
            yield self.lakeshore.set_heater_range(1,0)
            cur_temp = yield self.lakeshore.read_temp()
            cur_temp = cur_temp.split(';')[0]
            print('Temperature is ', cur_temp)

            yield self.lakeshore.set_p(1, cur_temp)
            yield self.lakeshore.ramp(1, 0, 0)

    def refresh(self):
        """
        Refresh the widget

        return: None
        """
        self.equip['gate valve'].state = self.vrs.returnstate('gate valve')
        self.equip['chamber valve'].state = self.vrs.returnstate('chamber valve')
        self.equip['turbo pump'].state = self.vrs.returnstate('turbo pump')
        self.equip['scroll pump'].state = self.vrs.returnstate('scroll pump')
        self.equip['turbo valve'].state = self.vrs.returnstate('turbo valve')
        self.equip['leak valve'].state = self.rvc.returnstate()
        self.equip['evaporator shutter'].state = self.evss.returnstate()

        # self.equip['evaporator power'].state = self.tdk.onoff() # Have it keep track of state like the others

        '''
        Future Equipment integration
        '''
        # self.equip['effusion power'].state = self.
        # self.equip['sputterer power'].state = self.dcxs.returnstate()
        # self.equip['effusion shutter'].state = self.


        self.update()

    def stopprocess(self):
        """
        Called when the stop button in pop up window is pressed, aborts
        an active process.

        return: None
        """
        self.main.abort()

    def paintEvent(self, event):
        """
        Paints all the static elements.

        return: None
        """
        painter = QtGui.QPainter(self)
        pen = QtGui.QPen()

        pen.setWidth(4)
        pen.setColor(QtGui.QColor(0, 0, 255))  # r, g, b
        painter.setPen(pen)

        #####Main vacuum part######
        # Leak valve#
        painter.drawLine(140-50, 358, 175-50, 358)  # (80, 358) -> (140, 358)
        painter.drawLine(60-50, 358, 80-50, 358)

        # gate valve
        painter.drawLine(175-50, 390, 150-50, 390)  # (150, 460) -> (150, 520)
        painter.drawLine(150-50, 390, 150-50, 460)
        painter.drawLine(150-50, 520, 150-50, 550)

        # scroll valve
        painter.drawLine(150-50, 430, 270-50, 430)  # (270, 430) -> (330, 430)
        painter.drawLine(330-50, 430, 475-50, 430)

        # turbo valve
        painter.drawLine(425-50, 430, 425-50, 460)  # (425, 460) -> (425, 520)
        painter.drawLine(425-50, 520, 425-50, 550)

        # turbo pump
        painter.drawLine(150-50, 550, 280-50, 550)  # (270, 550) -> (330, 550)
        painter.drawLine(320-50, 550, 425-50, 550)

        # Evaporator
        pen.setColor(QtGui.QColor(255, 0, 0))
        painter.setPen(pen)
        painter.drawLine(185-50, 275, 185-50, 230)  # (185, 250) -> (185, 190)
        painter.drawLine(185-50, 190, 185-50, 150)

        # Effusion
        pen.setColor(QtGui.QColor(20, 30, 30))
        painter.setPen(pen)
        painter.drawLine(350-50, 275, 350-50, 230)  # (350, 250) -> (350, 190)
        painter.drawLine(350-50, 190, 350-50, 150)

        # Sputterer
        pen.setColor(QtGui.QColor(20, 100, 30))
        painter.setPen(pen)
        painter.drawLine(425-50, 358, 475-50, 358)  # (475, 250) -> (475, 190)
        painter.drawLine(475-50, 358, 475-50, 150)

        pen.setWidth(4)
        pen.setColor(QtGui.QColor(0, 0, 0))  # r, g, b
        painter.setPen(pen)
        painter.drawRects(QtCore.QRect(175-50, 275, 250, 125))

    def connect(self):
        """
        Connects to the LabRAD servers and prepares the devices to listen to the commands

        return: None
        """
        if self.isConnected:
            self.disconnect()
            self.isConnected = False
        self.cxn = labrad.connect('localhost', password='pass')

        # Connectors to the valve/relay controller, the rvc pressure controller,
        # the stepper controller and the power supply controller.
        self.vrs = self.cxn.valve_relay_server
        self.vrs.select_device()
        #Iden command added so that arduino will respond to first command given from GUI.
        self.vrs.iden()

        self.rvc = self.cxn.rvc_server
        self.rvc.select_device()

        self.evss = self.cxn.evaporator_shutter_server
        self.evss.select_device()

        self.tdk = self.cxn.power_supply_server
        self.tdk.select_device()
        self.tdk.adr('6')
        self.tdk.rmt_set('REM')

        self.ftm = self.cxn.ftm_server
        self.ftm.select_device()

        self.lakeshore = self.cxn.lakeshore_336
        self.lakeshore.select_device()

        '''
        Other Servers we may integrate later
        '''

        #self.dcxs = self.cxn.DCXS_power
        #self.dcxs.select_device()

        # self.turbo450 = self.cxn.turbo450
        # self.turbo450.select_device()

        self.isConnected = True
        self.refresh()

    def closeEvent(self, event):
        '''
        To make closing consistent with the other windows
        '''
        if hasattr(self, 'main'):
            self.main.closeEvent(event)
        else:
            event.accept()
    #
#

class Valve(QtWidgets.QPushButton):
    """
    Defines all the valves in the Widget
    """

    def __init__(self, EvaporatorWidget, posx, posy, orient, color, name):
        """
        param EvaporatorWidget: parent class
        param posx: left-most point
        param posy: top-most point
        param orient: Orientation 'hor' for horizontal or vertical otherwise
        param color: example QtGui.QColor(255, 255, 255)
        param name: name of the valve, i.e. 'gate valve'
        """
        super().__init__(EvaporatorWidget)
        self.parent = EvaporatorWidget
        self.state = True # True for open
        self.setToolTip('Open')
        self.posx = posx
        self.posy = posy
        self.orient = orient
        self.color = color
        self.name = name
        if self.orient == 'hor':
            self.move(self.posx, self.posy - 20)
            self.resize(60, 40)
        else:
            self.move(self.posx - 20, self.posy)
            self.resize(40, 60)

    def paintEvent(self, event):
        """
        Paints valve

        return: None
        """
        painter = QtGui.QPainter(self)
        brush = QtGui.QBrush()
        pen = QtGui.QPen()
        pen.setWidth(1)
        pen.setColor(QtGui.QColor(0, 0, 0))
        painter.setPen(pen)
        if not self.state:  # close
            brush.setColor(QtGui.QColor(255, 255, 255))
        else:  # open
            brush.setColor(QtGui.QColor(self.color))
        brush.setStyle(Qt.Dense1Pattern)
        painter.setBrush(brush)

        if self.orient == 'hor':
            points = QPolygon([
                QPoint(0, 0),
                QPoint(0, 40),
                QPoint(58, 0),
                QPoint(58, 40)
            ])
            painter.drawPolygon(points)
        else:
            points = QPolygon([
                QPoint(0, 0),
                QPoint(40, 0),
                QPoint(0, 58),
                QPoint(40, 58)
            ])
            painter.drawPolygon(points)
    @inlineCallbacks
    def toggle(self, c):
        """
        Change the state of the valve. If the process is active QMessageBox appears. You can stop the process
        by pressing 'Stop'. If you want ot pause the process or dismiss the action press 'Cancel'.

        return: None
        """
        # if self.parent.main.status == "active":
        #     msg = QtWidgets.QMessageBox()
        #     msg.setWindowTitle("System is active")
        #     msg.setText("Please pause or stop the recipe before activating the manual control.")
        #
        #     msg.setIcon(QtWidgets.QMessageBox.Critical)
        #
        #     stop = QtWidgets.QPushButton("Stop")
        #     msg.addButton(stop, QtWidgets.QMessageBox.YesRole)
        #     stop.clicked.connect(self.parent.stopprocess)
        #
        #     cancel = QtWidgets.QPushButton("Cancel")
        #     msg.addButton(cancel, QtWidgets.QMessageBox.YesRole)
        #     msg.setDefaultButton(cancel)
        #     msg.exec_()
        # else:
        if self.state:
            if self.name == 'leak valve':
                print(self.parent.equip[self.name].input.text())
                if self.parent.equip[self.name].input.text() == '':
                    ans = yield self.parent.rvc.close_valve()
                    print(ans)
                    self.state = False
                    self.setToolTip('Closed')
                    self.parent.equip[self.name].status = False
                    print(self.name + " manually closed")
                elif (self.parent.equip[self.name].input.text() == 'vent') or \
                     (self.parent.equip[self.name].input.text() == 'Vent'):
                    self.parent.equip[self.name].input.clear()
                    print('Venting')
                    yield self.parent.rvc.set_mode_flo()
                    yield self.parent.rvc.set_nom_flo('100.0')
                else:
                    prs = self.parent.equip[self.name].input.text()
                    # prs = "{:.2E}".format(prs)
                    self.parent.equip[self.name].input.clear()
                    yield self.parent.rvc.set_mode_prs()

                    yield self.parent.rvc.set_nom_prs(prs)
            else:
                self.state = False
                self.setToolTip('Closed')
                self.parent.equip[self.name].status = False
                print(self.name + " manually closed")
                if self.name == 'gate valve':
                    yield self.parent.vrs.gate_close()
                elif self.name == 'chamber valve':
                    yield self.parent.vrs.chamber_valve_close()
                elif self.name == 'turbo valve':
                    yield self.parent.vrs.turbo_valve_close()
                else:
                    print('Incorrect name')
        else:
            self.state = True
            self.setToolTip('Open')
            self.parent.equip[self.name].status = True
            print(self.name + " manually opened")
            if self.name == 'gate valve':
                yield self.parent.vrs.gate_open()
            elif self.name == 'chamber valve':
                yield self.parent.vrs.chamber_valve_open()
            elif self.name == 'turbo valve':
                yield self.parent.vrs.turbo_valve_open()
            elif self.name == 'leak valve':
                if self.parent.equip[self.name].input.text() == '':
                    prs = str('5.00E-03')
                    print(prs)
                    ans = yield self.parent.rvc.set_mode_prs()
                    print(ans)

                    ans = yield self.parent.rvc.set_nom_prs(prs)
                    print(ans)
                elif (self.parent.equip[self.name].input.text() == 'vent') or \
                     (self.parent.equip[self.name].input.text() == 'Vent'):
                    self.parent.equip[self.name].input.clear()
                    print('Venting')
                    yield self.parent.rvc.set_mode_flo()
                    yield self.parent.rvc.set_nom_flo('100.0')
                else:
                    prs = self.parent.equip[self.name].input.text()
                    print(prs)
                    self.parent.equip[self.name].input.clear()
                    ans = yield self.parent.rvc.set_mode_prs()
                    print(ans)
                    ans = yield self.parent.rvc.set_nom_prs(str(prs))
                    print(ans)
            else:
                print('Incorrect name')
        self.update()

    def popup_clicked(self, i):
        """
        What to do in case any button on QMessageBox is pressed.

        :param i: message
        :return: None
        """
        if i.text() == 'Cancel':
            pass
        elif i.text() == 'Stop':
            self.parent.stopprocess()


class Pump(QtWidgets.QPushButton):
    """
    Defines all the pumps in the Widget
    """

    def __init__(self, EvaporatorWidget, posx, posy, name):
        """
        param EvaporatorWidget: parent class
        param posx: left-most point
        param posy: top-most point
        param name: name of the valve, i.e. 'turbo pump'
        """
        super().__init__(EvaporatorWidget)
        self.parent = EvaporatorWidget
        self.state = False # True for on
        self.setToolTip('Off')
        self.posx = posx
        self.posy = posy
        self.name = name
        self.move(self.posx, self.posy)
        self.resize(41, 41)

    def paintEvent(self, event):
        """
        Paints pump

        return: None
        """
        painter = QtGui.QPainter(self)
        brush = QtGui.QBrush()

        if not self.state:  # close
            brush.setColor(QtGui.QColor(255, 255, 255))
            brush.setStyle(Qt.Dense1Pattern)
            painter.setBrush(brush)
            painter.drawEllipse(0, 0, 40, 40)
        else:  # open
            brush.setColor(QtGui.QColor("#FFD141"))
            brush.setStyle(Qt.Dense1Pattern)
            painter.setBrush(brush)
            painter.drawEllipse(0, 0, 40, 40)

    def toggle(self):
        """
        Change the state of the pump. If the process is active QMessageBox appears. You can stop the process
        by pressing 'Stop'. If you want ot pause the process or dismiss the action press 'Cancel'.

        return: None
        """
        # if self.parent.main.status == "active":
        #     msg = QtWidgets.QMessageBox()
        #     msg.setWindowTitle("System is active")
        #     msg.setText("Please pause or stop the recipe before activating the manual control.")
        #
        #     msg.setIcon(QtWidgets.QMessageBox.Critical)
        #
        #     stop = QtWidgets.QPushButton("Stop")
        #     msg.addButton(stop, QtWidgets.QMessageBox.YesRole)
        #     stop.clicked.connect(self.parent.stopprocess)
        #
        #     cancel = QtWidgets.QPushButton("Cancel")
        #     msg.addButton(cancel, QtWidgets.QMessageBox.YesRole)
        #     msg.setDefaultButton(cancel)
        #     msg.exec_()
        # elif self.name == 'scroll pump' and self.state and self.parent.equip['turbo pump'].state:
        #     msg = QtWidgets.QMessageBox()
        #     msg.setWindowTitle("Turbo Pump Active")
        #     msg.setText("Cannot turn off the scroll pump while the turbo pump is running.")
        #
        #     msg.setIcon(QtWidgets.QMessageBox.Critical)
        #     cancel = QtWidgets.QPushButton("Continue")
        #     msg.addButton(cancel, QtWidgets.QMessageBox.YesRole)
        #     msg.setDefaultButton(cancel)
        #     msg.exec_()
        # elif self.name == 'turbo pump' and not self.state and (not self.parent.equip['scroll pump'].state or not self.parent.equip['turbo valve'].state):
        #     msg = QtWidgets.QMessageBox()
        #     msg.setWindowTitle("Scroll Pump Off")
        #     msg.setText("Cannot turn on turbo with the scroll pump off or turbo valve closed.")
        #
        #     msg.setIcon(QtWidgets.QMessageBox.Critical)
        #     cancel = QtWidgets.QPushButton("Continue")
        #     msg.addButton(cancel, QtWidgets.QMessageBox.YesRole)
        #     msg.setDefaultButton(cancel)
        #     msg.exec_()
        # else:
        if self.state:
            self.state = False
            self.setToolTip('Off')
            self.parent.equip[self.name].status = False
            print(self.name + " manually turned off")
            if self.name == 'turbo pump':
                self.parent.vrs.turbo_off()
            elif self.name == 'scroll pump':
                self.parent.vrs.scroll_off()
            else:
                print('Incorrect Pump Name')
        else:
            self.state = True
            self.setToolTip('On')
            self.parent.equip[self.name].status = True
            print(self.name + " manually turned on")
            if self.name == 'turbo pump':
                self.parent.vrs.turbo_on()
            elif self.name == 'scroll pump':
                self.parent.vrs.scroll_on()
            else:
                print('Incorrect Pump Name')
        self.update()

    def popup_clicked(self, i):
        """
        What to do in case any button on QMessageBox is pressed.

        param i: message
        return: None
        """
        if i.text() == 'Cancel':
            pass
        elif i.text() == 'Stop':
            self.parent.stopprocess()


class Power(QtWidgets.QPushButton):
    """
    Defines all the power supplies in the Widget
    """

    def __init__(self, EvaporatorWidget, posx, posy, name):
        """
        param EvaporatorWidget: parent class
        param posx: left-most point
        param posy: top-most point
        param name: name of the valve, i.e. 'turbo pump'
        """
        super().__init__(EvaporatorWidget)
        self.parent = EvaporatorWidget
        self.state = False # True for on
        self.setToolTip('Off')
        self.posx = posx
        self.posy = posy
        self.name = name
        self.move(self.posx, self.posy)
        self.resize(41, 41)

    def paintEvent(self, event):
        """
        Paints power supply

        return: None
        """
        painter = QtGui.QPainter(self)
        brush = QtGui.QBrush()

        if not self.state:  # close
            brush.setColor(QtGui.QColor(255, 255, 255))
            brush.setStyle(Qt.Dense1Pattern)
            painter.setBrush(brush)
            painter.drawEllipse(0, 0, 40, 40)
        else:  # open
            brush.setColor(QtGui.QColor("#FFD141"))
            brush.setStyle(Qt.Dense1Pattern)
            painter.setBrush(brush)
            painter.drawEllipse(0, 0, 40, 40)

    def toggle(self):
        """
        Change the state (On/Off) of the power supply. Can be accessed only from the main window.

        return: None
        """
        if self.state:
            self.state = False
            self.setToolTip('Off')
            self.parent.equip[self.name].status = False  # Not sure we need that
        else:
            self.state = True
            self.setToolTip('On')
            self.parent.equip[self.name].status = True  # Not sure we need that
        self.update()


class Shutter(QtWidgets.QPushButton):
    """
    Defines all the shutters in the Widget
    """

    def __init__(self, EvaporatorWidget, posx, posy, orient, color, name):
        super().__init__(EvaporatorWidget)
        self.name = name
        self.parent = EvaporatorWidget
        self.state = False # True for Open
        self.setToolTip('Closed')
        self.posx = posx
        self.posy = posy
        self.orient = orient
        self.color = color
        if self.orient == 'hor':
            self.move(self.posx, self.posy + 2)
            self.resize(60, 40)
        else:
            self.move(self.posx - 4, self.posy)
            self.resize(40, 60)

        """First define the line for open and close position for each valve"""
        # close
        if orient == 'hor':
            self.close = QLine(0, 4, 35, 19)
        else:
            self.close = QLine(4, 0, 19, 35)
        # open
        if orient == 'hor':
            self.open = QLine(5, 4, 35, 4)
        else:
            self.open = QLine(4, 5, 4, 35)

    def paintEvent(self, event):
        """
        Paints shutter

        return: None
        """
        painter = QtGui.QPainter(self)
        pen_close = QtGui.QPen()
        pen_close.setWidth(4)
        pen_close.setColor(QtGui.QColor(self.color))  # r, g, b
        pen_open = QtGui.QPen()
        pen_open.setWidth(4)
        pen_open.setColor(QtGui.QColor(self.color))

        if not self.state:  # close
            painter.setPen(pen_close)
            painter.drawLine(self.close)
        else:  # open
            painter.setPen(pen_open)
            painter.drawLine(self.open)

    def toggle(self):
        """
        Change the state (Open/Closed) of the shutter. Can be accessed only from the main window.

        return: None
        """
        if self.state:
            self.state = False
            self.setToolTip('Closed')
            if self.name == 'evaporator shutter':
                self.parent.evss.close_shutter()
                print('closed evaporator shutter')
            elif self.name == 'effusion shutter':
                self.parent.evss.close_effusion_shutter()
                print('closed evaporator shutter')
        else:
            self.state = True
            self.setToolTip('Open')
            if self.name == 'evaporator shutter':
                self.parent.evss.open_shutter()
                print('opened evaporator shutter')
            elif self.name == 'effusion shutter':
                self.parent.evss.open_effusion_shutter()
                print('opened evaporator shutter')
        self.update()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ex = EvaporatorWidget(None)
    ex.show()
    sys.exit(app.exec_())
