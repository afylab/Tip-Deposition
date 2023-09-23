# Copyright []
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
### BEGIN NODE INFO
[info]
name = SIM900
version = 1.0
description = SIM 900 Mainframe with SIM 921 AC Resistance Bridge and SIM 928 Isolated Voltage Source
[startup]
cmdline = %PYTHON% %FILE%
timeout = 20
[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

import platform
global serial_server_name
serial_server_name = platform.node() + '_serial_server'
import numpy as np
from labrad.server import setting
from labrad.devices import DeviceServer,DeviceWrapper
from twisted.internet.defer import inlineCallbacks, returnValue
import labrad.units as units
from labrad.types import Value

TIMEOUT = Value(5,'s')
BAUD    = 9600
PARITY = 'N'
STOP_BITS = 1
BYTESIZE= 8

class serverInfo(object):
    def __init__(self):
        self.deviceName = 'sim921'
        self.serverName = "sim921"

    def getDeviceName(self,comPort):
        return "%s (%s)"%(self.serverName, comPort)


class SIM921Wrapper(DeviceWrapper):

    @inlineCallbacks
    def connect(self, server, port):
        """Connect to a device."""
        print('connecting to "%s" on port "%s"...' % (server.name, port), end=' ')
        self.server = server
        self.ctx = server.context()
        self.port = port
        p = self.packet()
        p.open(port)
        print('opened on port "%s"' %self.port)
        p.baudrate(BAUD)
        p.parity(PARITY)
        p.stopbits(STOP_BITS)
        p.bytesize(BYTESIZE)
        p.read()  # clear out the read buffer
        p.timeout(TIMEOUT)
        print(" CONNECTED ")
        yield p.send()

    def packet(self):
        """Create a packet in our private context."""
        return self.server.packet(context=self.ctx)

    def shutdown(self):
        """Disconnect from the serial port when we shut down."""
        return self.packet().close().send()

    @inlineCallbacks
    def write(self, code):
        """Write a data value to the temperature controller."""
        yield self.packet().write(code).send()

    @inlineCallbacks
    def read(self):
        p=self.packet()
        p.read_line()
        ans=yield p.send()
        returnValue(ans.read)

    @inlineCallbacks
    def query(self, code):
        """ Write, then read. """
        p = self.packet()
        p.write(code)
        p.read_line()
        ans = yield p.send()
        returnValue(ans.read_line)


class SIM921Server(DeviceServer):
    name = serverInfo().serverName
    deviceName = serverInfo().deviceName
    deviceWrapper = SIM921Wrapper

    @inlineCallbacks
    def initServer(self):
        print('loading config info...', end=' ')
        self.reg = self.client.registry()
        yield self.loadConfigInfo()
        print('done.')
        print(self.serialLinks)
        yield DeviceServer.initServer(self)

    @inlineCallbacks
    def loadConfigInfo(self):
        """Load configuration information from the registry."""
        # reg = self.client.registry
        # p = reg.packet()
        # p.cd(['', 'Servers', 'Heat Switch'], True)
        # p.get('Serial Links', '*(ss)', key='links')
        # ans = yield p.send()
        # self.serialLinks = ans['links']
        reg = self.reg
        yield reg.cd(['', 'Servers', 'SIM921', 'Links'], True)
        dirs, keys = yield reg.dir()
        p = reg.packet()
        print(" created packet")
        print("printing all the keys",keys)
        for k in keys:
            print("k=",k)
            p.get(k, key=k)

        ans = yield p.send()
        print("ans=",ans)
        self.serialLinks = dict((k, ans[k]) for k in keys)


    @inlineCallbacks
    def findDevices(self):
        """Find available devices from list stored in the registry."""
        devs = []
        # for name, port in self.serialLinks:
        # if name not in self.client.servers:
        # continue
        # server = self.client[name]
        # ports = yield server.list_serial_ports()
        # if port not in ports:
        # continue
        # devName = '%s - %s' % (name, port)
        # devs += [(devName, (server, port))]
        # returnValue(devs)
        for name, (serServer, port) in list(self.serialLinks.items()):
            if serServer not in self.client.servers:
                continue
            server = self.client[serServer]
            print(server)
            print(port)
            ports = yield server.list_serial_ports()
            print(ports)
            if port not in ports:
                continue
            devName = '%s - %s' % (serServer, port)
            devs += [(devName, (server, port))]

       # devs += [(0,(3,4))]
        returnValue(devs)

    @setting(100)
    def connect(self,c,server,port):
        dev=self.selectedDevice(c)
        yield dev.connect(server,port)

    @setting(101,returns='s')
    def ID(self,c):
        dev=self.selectedDevice(c)
        ans=yield dev.query("*IDN?\r")
        returnValue(ans)

    @setting(301,freq='v')
    def set_frequency(self,c,freq, channel = 7):
        dev=self.selectedDevice(c)
        yield dev.write('SNDT 7,"FREQ %s"\r'%(channel,freq))

    @setting(302,returns='v')
    def get_frequency(self,c,channel=7):
        dev=self.selectedDevice(c)
        yield dev.write('CONN %s,"cometzir"\r'%channel)
        ans=yield dev.query('FREQ?\r')
        yield dev.write('cometzir\r')
        returnValue(float(ans))

    @setting(303,range='i')
    def set_range(self,c,range,channel=7):
        dev=self.selectedDevice(c)
        yield dev.write('SNDT %s,"RANG %s"\r'%(channel,range))

    @setting(304,returns='s')
    def get_range(self,c,channel=7):
        dev=self.selectedDevice(c)
        yield dev.write('CONN %s,"cometzir"\r'%channel)
        ans=yield dev.query('RANG?\r')
        yield dev.write('cometzir\r')
        returnValue(ans)

    @setting(305,excitation='i')
    def set_excitation(self,c,excitation,channel=7):
        dev=self.selectedDevice(c)
        yield dev.write('SNDT %s,"EXCI %s"\r'%(channel,excitation))

    @setting(306,returns='s')
    def get_excitation(self,c,channel=7):
        dev=self.selectedDevice(c)
        yield dev.write('CONN %s,"cometzir"\r'%channel)
        ans=yield dev.query('EXCI?\r')
        yield dev.write('cometzir\r')
        returnValue(ans)

    @setting(307)
    def excitation_on(self,c,channel=7):
        dev=self.selectedDevice(c)
        yield dev.write('SNDT %s,"EXON 1"\r'%(channel))

    @setting(308)
    def excitation_off(self,c,channel=7):
        dev=self.selectedDevice(c)
        yield dev.write('SNDT %s,"EXON 0"\r'%(channel))

    @setting(309,returns='s')
    def get_excitation_state(self,c,channel=7):
        dev=self.selectedDevice(c)
        yield dev.write('CONN %s,"cometzir"\r'%channel)
        ans=yield dev.query('EXCI?\r')
        yield dev.write('cometzir\r')
        returnValue(ans)

    @setting(310,mode='i')
    def set_excitation_mode(self,c,mode,channel=7):
        dev=self.selectedDevice(c)
        yield dev.write('SNDT %s,"MODE %s"\r'%(channel,mode))

    @setting(311,returns='s')
    def get_excitation_mode(self,c,channel=7):
        dev=self.selectedDevice(c)
        yield dev.write('CONN %s,"cometzir"\r'%channel)
        ans=yield dev.query('MODE?\r')
        yield dev.write('cometzir\r')
        returnValue(ans)

    @setting(312,time_constant='i')
    def set_time_constant(self,c,time_constant,channel=7):
        dev=self.selectedDevice(c)
        yield dev.write('SNDT %s,"TCON %s"\r'%(channel,time_constant))

    @setting(313,returns='s')
    def get_time_constant(self,c,channel=7):
        dev=self.selectedDevice(c)
        yield dev.write('CONN %s,"cometzir"\r'%channel)
        ans=yield dev.query('TCON?\r')
        yield dev.write('cometzir\r')
        returnValue(ans)

    @setting(314,returns='v')
    def get_excitation_voltage(self,c,channel=7):
        dev=self.selectedDevice(c)
        yield dev.write('CONN %s,"cometzir"\r'%channel)
        ans=yield dev.query('VEXC?\r')
        yield dev.write('cometzir\r')
        returnValue(float(ans))

    @setting(315,returns='v')
    def measure_excitation_current(self,c,channel=7):
        dev=self.selectedDevice(c)
        yield dev.write('CONN %s,"cometzir"\r'%channel)
        ans=yield dev.query('IEXC?\r')
        yield dev.write('cometzir\r')
        returnValue(float(ans))

    @setting(316,returns='v')
    def measure_phase(self,c,channel=7):
        dev=self.selectedDevice(c)
        yield dev.write('CONN %s,"cometzir"\r'%channel)
        ans=yield dev.query('PHAS?\r')
        yield dev.write('cometzir\r')
        returnValue(float(ans))

    @setting(317,returns='v')
    def measure_resistance(self,c,channel=7):
        dev=self.selectedDevice(c)
        yield dev.write('CONN %s,"cometzir"\r'%channel)
        ans=yield dev.query('RVAL?\r')
        yield dev.write('cometzir\r')
        if abs(float(ans)) > 5000:
            ans = 5000
        returnValue(ans)

    @setting(319)
    def ACRB_reset(self,c,channel=7):
        dev=self.selectedDevice(c)
        yield dev.write('SNDT %s,"*RST"\r'%channel)

__server__ = SIM921Server()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
