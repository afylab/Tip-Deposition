#LabRAD Servers and GUI for nanoscale SQUID on TIP (nSOT) fabrication

***

This program is a re-design based on earlier versions of the Evaporator software. The new
version incorporates the sputtering system and effusion cell in addition to the thermal
evaporator. This program is designed to allow more flexibility in the design of the Tip
Deposition Software. The idea is to create a Recipe object that contains the instructions
for fabricating a particular type of nanoSQUID tip in a simple sequence of readable steps
and have the rest of the process handled behind the scenes.

Requirements:
Python 3.7+ (Python 3.7 or higher is required to maintain insertion order of keys in dictionaries.
This program is unstable without lower versions.)
pyqtgraph
pylabrad

***
Instructions:


***

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
