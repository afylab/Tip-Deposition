'''
A test server, replicates a piece of hardware with a dummy sensor value and an output value.
The sensor value is proportial a moving average of the output value with some random noise
sensor = C*output*alpha + (1-alpha)*sensor) + noise(std)
Where:
C : coefficient that relates output to sensor, randomly selected at start but editable
alpha : averaging factor, number between 0 and 1
noise : Gaussian noise with zero average and standard deviation, std.

Also includes a clock, accessible with get_time

Used for basic testing of equipment handler and process.
'''

from labrad.server import LabradServer, setting
#from twisted.internet.defer import inlineCallbacks

from numpy.random import normal, uniform
from traceback import format_exc
from datetime import datetime

# For Testing Purposes
class DummyHardware(LabradServer):
	name = "Dummy"

	#@inlineCallbacks
	def initServer(self):
		self.sensor = 0
		self.output = 0
		self.C = uniform(1,2)
		self.alpha = 0.05
		self.std = 0.5
	#

	@setting(10)
	def set_output(self, c, val):
		try:
			self.output = float(val)
		except:
			print(format_exc())
	#


	@setting(11, returns='v')
	def query(self, c):
		self.sensor = self.C*self.output*self.alpha + (1-self.alpha)*self.sensor + normal(0, self.std)
		return self.sensor
	#

	@setting(12)
	def set_coefficient(self, c, coeff):
		'''
		Set the coefficient.
		'''
		try:
			self.C = float(coeff)
		except:
			print(format_exc())
	#

	@setting(13)
	def set_alpha(self, c, alpha):
		'''
		Set the coefficient.
		'''
		try:
			if alpha is not None:
				if alpha < 0 or alpha > 1:
					raise ValueError("Alpha too big")
				self.alpha = float(alpha)
		except:
			print(format_exc())
	#

	@setting(14, returns='s')
	def get_time(self, c):
		return datetime.now().strftime('%H:%M:%S')
	#

	@setting(15, returns='v')
	def get_output(self, c):
		return self.output
	#

	@setting(16)
	def reset(self, c):
		self.signal = 0
		self.output = 0
	#
#

__server__ = DummyHardware()
if __name__ == '__main__':
	from labrad import util
	util.runServer(__server__)
