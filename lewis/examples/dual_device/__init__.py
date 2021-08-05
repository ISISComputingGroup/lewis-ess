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

from lewis.adapters.epics import PV, EpicsInterface
from lewis.adapters.stream import StreamInterface, Var
from lewis.core.utils import check_limits
from lewis.devices import Device


class VerySimpleDevice(Device):
    upper_limit = 100
    lower_limit = 0

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
    @check_limits("lower_limit", "upper_limit")
    def second(self, new_second):
        self._second = new_second


class VerySimpleInterface(EpicsInterface):
    """
    This is the EPICS interface to a quite simple device. It offers 5 PVs that expose
    different things that are part of the device, the interface or neither.
    """

    pvs = {
        "Param-Raw": PV("param", type="int", doc="The raw underlying parameter."),
        "Param": PV(("get_param", "set_param"), type="int"),
        "Second": PV("second", meta_data_property="param_raw_meta"),
        "Second-Int": PV("second_int", type="int"),
        "Constant": PV(lambda: 4, doc="A constant number."),
    }

    @property
    def param_raw_meta(self):
        return {"lolo": self.device.lower_limit, "hihi": self.device.upper_limit}

    @property
    def second_int(self):
        """The second parameter as an integer."""
        return int(self.device.second)


class VerySimpleStreamInterface(StreamInterface):
    """This is a TCP stream interface to the epics device, which only exposes param."""

    commands = {
        Var(
            "param",
            read_pattern=r"P\?$",
            write_pattern=r"P=(\d+)",
            argument_mappings=(int,),
            doc="An integer parameter.",
        )
    }

    in_terminator = "\r\n"
    out_terminator = "\r\n"
