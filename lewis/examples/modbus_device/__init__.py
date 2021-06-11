# -*- coding: utf-8 -*-
# *********************************************************************
# lewis - a library for creating hardware device simulators
# Copyright (C) 2016-2021 European Spallation Source ERIC
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

from lewis.adapters.modbus import ModbusBasicDataBank, ModbusInterface
from lewis.devices import Device


class ModbusDevice(Device):
    pass


class ExampleModbusInterface(ModbusInterface):
    """
    The class attributes di, co, ir and hr represent Discrete Inputs, Coils, Input Registers and
    Holding Registers, respectively. Each attribute should be assigned a ModbusDataBank instance
    by the Interface implementation.

    Here, two basic ModbusDataBanks are created and initialized to a default value across the full
    range of valid addresses. One DataBank is shared by di and co, and the other by ir and hr to
    demonstrate overlaid memory segments. If you want each segment to have its own memory, just
    create separate instances for all four.
    """

    di = ModbusBasicDataBank(False)
    co = di
    ir = ModbusBasicDataBank(0)
    hr = ir
