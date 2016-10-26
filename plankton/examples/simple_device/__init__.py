#  -*- coding: utf-8 -*-
# *********************************************************************
# plankton - a library for creating hardware device simulators
# Copyright (C) 2016 European Spallation Source ERIC
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

from plankton.devices import Device

from plankton.adapters.stream import StreamAdapter, Cmd


class VerySimpleDevice(Device):
    param = 10


class VerySimpleInterface(StreamAdapter):
    commands = {
        Cmd('get_param', '^P$'),
        Cmd('set_param', '^P=(.+)$'),
    }

    in_terminator = '\r\n'
    out_terminator = '\r\n'

    def get_param(self):
        return self._device.param

    def set_param(self, new_param):
        self._device.param = new_param

    def handle_error(self, request, error):
        return 'An error occurred: ' + repr(error)
