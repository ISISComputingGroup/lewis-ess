# -*- coding: utf-8 -*-
# *********************************************************************
# lewis - a library for creating hardware device simulators
# Copyright (C) 2016-2017 European Spallation Source ERIC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# *********************************************************************

from lewis.devices import Device

from lewis.adapters.epics import EpicsAdapter, PV


class VerySimpleDevice(Device):
    param = 10
    _second = 2.0

    def get_param(self):
        """The parameter multiplied by 2."""
        return self.param * 2

    def set_param(self, new_param):
        self.param = int(new_param / 2)

    @property
    def second(self):
        """A second (floating point) parameter."""
        return self._second

    @second.setter
    def second(self, new_second):
        self._second = new_second


class VerySimpleInterface(EpicsAdapter):
    """
    This is the EPICS interface to a quite simple device. It offers 5 PVs that expose
    different things that are part of the device, the interface or neither.
    """
    pvs = {
        'Param-Raw': PV('param', type='int', doc='The raw underlying parameter.'),
        'Param': PV(('get_param', 'set_param'), type='int'),
        'Second': PV('second'),
        'Second-Int': PV('second_int', type='int', read_only=True),
        'Constant': PV(lambda: 4, doc='A constant number.')
    }

    @property
    def second_int(self):
        """The second parameter as an integer."""
        return int(self.device.second)


framework_version = '1.0.2'
