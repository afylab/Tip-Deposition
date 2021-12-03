"""
### BEGIN NODE INFO
[info]
name = DCXS power
version = 1.0
description = DCXS sputtering gun power supply controller.

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from labrad.server import setting
from labrad.devices import DeviceServer, DeviceWrapper
from twisted.internet.defer import inlineCallbacks
from twisted.internet import reactor, defer
from labrad.types import Value
from time import sleep
import serial
TIMEOUT = Value(2, 's')
BAUD = 38400
BYTESIZE = 8
STOPBITS = 1
PARITY = serial.PARITY_NONE


class DCXSPowerWrapper(DeviceWrapper):

    @inlineCallbacks
    def connect(self, server, port):
        """Connect to a device."""
        print('connecting to "%s" on port "%s"...' % (server.name, port), end=' ')
        self.server = server
        self.ctx = server.context()
        self.port = port
        p = self.packet()
        p.open(port)
        p.baudrate(BAUD)
        p.bytesize(BYTESIZE)
        p.stopbits(STOPBITS)
        p.setParity = PARITY
        p.timeout(TIMEOUT)
        p.read()  # clear out the read buffer
        # Set timeout to 0
        p.timeout(None)
        print(" CONNECTED ")
        yield p.send()

    def packet(self):
        """Create a packet in our private context"""
        return self.server.packet(context=self.ctx)

    def shutdown(self):
        """Disconnect from the serial port when we shut down"""
        return self.packet().close().send()

    @inlineCallbacks
    def write(self, code):
        """Write a data value to the device"""
        yield self.packet().write(code).send()

    # @inlineCallbacks
    # def read(self):
    #     """Read a response line from the device"""
    #     p = self.packet()
    #     p.read()
    #     ans = yield p.send()
    #     return ans.read
    #
    # @inlineCallbacks
    # def query(self, code):
    #     """ Write, then read. """
    #     p = self.packet()
    #     p.timeout(TIMEOUT)
    #     p.write(code)
    #     p.read()
    #     ans = yield p.send()
    #     return ans.read

    @inlineCallbacks
    def read(self):
        """Read a response line from the device"""
        p=self.packet()
        p.read_line()
        ans=yield p.send()
        return ans.read_line

    @inlineCallbacks
    def query(self, code):
        """ Write, then read. """
        p = self.packet()
        p.write(code)
        p.read_line()
        ans = yield p.send()
        return ans.read_line

class PowerSupplyServer(DeviceServer):
    name = 'DCXS_power'
    deviceName = 'DCXS Power'
    deviceWrapper = DCXSPowerWrapper

    def __init__(self):
        super().__init__()
        self.state = False
        self.abort = False

    @inlineCallbacks
    def initServer(self):
        print('loading config info...', end=' ')
        self.reg = self.client.registry()
        yield self.loadConfigInfo()
        print('done.')
        print(self.serialLinks)
        yield DeviceServer.initServer(self)
        self.busy = False

    @inlineCallbacks
    def loadConfigInfo(self):
        reg = self.reg
        yield reg.cd(['', 'Servers', 'DCXS Power', 'Links'], True)
        dirs, keys = yield reg.dir()
        p = reg.packet()
        print("Created packet")
        print("printing all the keys", keys)
        for k in keys:
            print("k=", k)
            p.get(k, key=k)
        ans = yield p.send()
        print("ans=", ans)
        self.serialLinks = dict((k, ans[k]) for k in keys)

    @inlineCallbacks
    def findDevices(self):
        devs = []
        for name, (serServer, port) in self.serialLinks.items():
            if serServer not in self.client.servers:
                print(serServer)
                print(self.client.servers)
                continue
            server = self.client[serServer]
            ports = yield server.list_serial_ports()
            if port not in ports:
                continue
            devName = '%s - %s' % (serServer, port)
            devs += [(devName, (server, port))]
        return devs

    @setting(10, state='s', start_setpoint='i', end_setpoint='i', ramprate='i', returns='?')
    def switch(self, c, state, start_setpoint=10, end_setpoint=10, ramprate=10):
        """Turn on or off a scope channel display.
        State must be in [A - ON, B - OFF].
        Channel must be int or string.
        Setpoint is the power at which sputtering should happen.
        Ramprate is in W/min, 10-20 W/min is recommended.
        """
        dev = self.selectedDevice(c)
        if state is not None:
            if state not in ['A', 'B']:
                raise Exception('state must be A - ON, B - OFF')
            else:
                cur_output = yield self.set_setpoint(c, start_setpoint)
                yield dev.write(state.encode("ASCII", "ignore"))
                yield self.sleep(0.1)
                self.state = not self.state
            if state == 'A':
                self.state = not self.state
                if end_setpoint != 10:
                    yield self.sleep(2)
                    output_quant = ramprate / 60
                    cur_output_step = cur_output
                    print(output_quant)
                    print(cur_output)
                    print((end_setpoint-cur_output)/ramprate)
                    while (cur_output != end_setpoint) and not self.abort:
                        cur_output_step = cur_output_step + output_quant * abs(end_setpoint-cur_output)/(end_setpoint-cur_output)
                        if abs(cur_output_step - cur_output) >= 1:
                            cur_output = yield self.set_setpoint(c, round(cur_output_step))
                        print('cur_output = ', str(cur_output), ' cur_output_step = ', str(cur_output_step))
                        yield self.sleep(1)
                    if self.abort:
                        yield dev.write('B'.encode("ASCII", "ignore"))
                        self.abort = False
            resp = state
        return resp

    @setting(11, p='?')
    def mode(self, c, p=None):
        """Get or set the regulation mode: 0 - Power, 1 - Voltage, 2 - Current"""
        dev = self.selectedDevice(c)
        if p is None:
            mode = yield dev.query(b'c')
        elif p in [0, 1, 2]:
            yield dev.write(('D' + str(p)).encode("ASCII", "ignore"))
            # yield self.sleep(0.1)
            yield dev.write('c')
            yield self.sleep(0.1)
            mode = yield dev.read()
        else:
            raise Exception('p should be 0, 1 or 2')
        return mode

    @setting(12, p='?', returns='?')
    def set_setpoint(self, c, p=None):
        """Get or set the set point (not the actual!) power, voltage or
        current (0 - 20) depending on what regime is chosen. It's the setpoint
        right after the ignition, you will need to set the setpoint for
        sputtering in the switch function."""
        dev = self.selectedDevice(c)
        print('setpoint is ', p)
        if isinstance(p, (bool, str, list, dict, tuple, float)):
            raise Exception('Incorrect format, must be integer')
        if self.abort:
            yield dev.write('B'.encode("ASCII", "ignore"))
            self.abort = False
        elif isinstance(p, int) and (p >= 0) and (p < 351) and not self.abort:
            dec = len(str(p))
            out_p = '0' * (4 - dec) + str(p)
            yield dev.write(('C' + out_p).encode("ASCII", "ignore"))
            yield self.sleep(0.1)
            yield dev.write('b')
            yield self.sleep(0.1)
            setpoint = yield dev.read()
            try:
                setpoint = int(setpoint)
            except ValueError:
                print('Something wrong with the output setpoint.')
                print(setpoint)
            return setpoint
        elif p is None:
            # setpoint = yield dev.query('b')
            yield dev.write('b')
            yield self.sleep(0.1)
            setpoint = yield dev.read()
            # setpoint = yield dev.query('b'.encode("ASCII", "ignore"))
            try:
                setpoint = int(setpoint)
            except ValueError:
                print('Something wrong with the output setpoint.')
                print(setpoint)
            return setpoint
        else:
            raise Exception('set point should be 0 - 350')

    # @setting(13, returns='?')
    # def output_act(self, c):
    #     """Get the actual power, voltage or current (0 - 1000)
    #     depending on what regime is chosen."""
    #     dev = self.selectedDevice(c)
    #     mode = yield dev.query('c'.encode("ASCII", "ignore"))
    #     if mode == 0:
    #         p = yield dev.query('d'.encode("ASCII", "ignore"))
    #     elif mode == 1:
    #         p = yield dev.query('e'.encode("ASCII", "ignore"))
    #     else:
    #         p = yield dev.query('f'.encode("ASCII", "ignore"))
    #     try:
    #         p = int(p)
    #     except ValueError:
    #         print('Something wrong with the output. Check the hardware display.')
    #     return p

    @setting(13, returns='?')
    def power(self, c):
        """Get the actual power (0 - 1000)."""
        dev = self.selectedDevice(c)
        yield dev.write('d'.encode("ASCII", "ignore"))
        yield self.sleep(0.1)
        p = yield dev.read()
        try:
            p = int(p)
        except ValueError:
            print('Something wrong with the power reading. Check the hardware display.')
        return p

    @setting(14, returns='?')
    def voltage(self, c):
        """Get the actual voltage (0 - 1000)."""
        dev = self.selectedDevice(c)
        yield dev.write('e'.encode("ASCII", "ignore"))
        yield self.sleep(0.1)
        p = yield dev.read()
        try:
            p = int(p)
        except ValueError:
            print('Something wrong with the voltage reading. Check the hardware display.')
        return p

    @setting(15, returns='?')
    def current(self, c):
        """Get the actual current (0 - 1000)."""
        dev = self.selectedDevice(c)
        yield dev.write('f'.encode("ASCII", "ignore"))
        yield self.sleep(0.1)
        p = yield dev.read()
        try:
            p = int(p)
        except ValueError:
            print('Something wrong with the current reading. Check the hardware display.')
        return p

    # @setting(16, p='?', returns='?')
    # def ramptime(self, c, p=None):
    #     """Get or set (0 - 99s) the ramp time"""
    #     dev = self.selectedDevice(c)
    #     if p is None:
    #         yield dev.write('g'.encode("ASCII", "ignore"))
    #         # yield self.sleep(0.1)
    #         ramp_time = yield dev.read()
    #     elif isinstance(p, int) and (p >= 0) and (p < 100) and len(str(p)) < 3:
    #         dec = len(str(p))
    #         out_p = '0' * (2 - dec) + str(p)
    #         yield dev.write(('E'+out_p).encode("ascii", "ignore"))
    #         yield self.sleep(0.1)
    #         ramp_time = yield dev.read()
    #     else:
    #         raise Exception('ramp time should be 0 - 99s')
    #
    #     return ramp_time

    @setting(17, returns='?')
    def identification(self, c):
        """Get or set (0 - 99s) the ramp time"""
        dev = self.selectedDevice(c)
        yield dev.write('?'.encode("ASCII", "ignore"))
        # yield self.sleep(0.1)
        iden = yield dev.read()
        return iden

    @setting(18, returns='b')
    def returnstate(self, c):
        return self.state

    @setting(19, returns='?')
    def abort_ramp(self, c):
        self.abort = True
        return self.abort

    @setting(20, returns='?')
    def unlock(self, c):
        self.abort = False
        return self.abort

    def sleep(self,secs):
        d = defer.Deferred()
        reactor.callLater(secs,d.callback,'Sleeping')
        return d

__server__ = PowerSupplyServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
