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

from lewis.adapters.stream import Cmd, StreamInterface, Var


class JulaboStreamInterfaceV2(StreamInterface):
    """Julabos can have different commands sets depending on the version number of the hardware.

    This protocol matches that for: FP50-HE (unconfirmed).
    """

    protocol = "julabo-version-2"

    commands = {
        Var("temperature", read_pattern="^IN_PV_00$", doc="The bath temperature."),
        Var(
            "external_temperature",
            read_pattern="^IN_PV_01$",
            doc="The external temperature.",
        ),
        Var("heating_power", read_pattern="^IN_PV_02$", doc="The heating power."),
        Var(
            "set_point_temperature",
            read_pattern="^IN_SP_00$",
            doc="The temperature setpoint.",
        ),
        Cmd(
            "set_set_point",
            r"^OUT_SP_00 ([0-9]*\.?[0-9]+)$",
            argument_mappings=(float,),
        ),
        # Read pattern for high limit is different from version 1
        Var(
            "temperature_high_limit",
            read_pattern="^IN_SP_03$",
            doc="The high limit - usually set in the hardware.",
        ),
        # Read pattern for low limit is different from version 1
        Var(
            "temperature_low_limit",
            read_pattern="^IN_SP_04$",
            doc="The low limit - usually set in the hardware.",
        ),
        Var("version", read_pattern="^VERSION$", doc="The Julabo version."),
        Var("status", read_pattern="^STATUS$", doc="The Julabo status."),
        Var(
            "is_circulating",
            read_pattern="^IN_MODE_05$",
            doc="Whether it is circulating.",
        ),
        Cmd("set_circulating", "^OUT_MODE_05 (0|1)$", argument_mappings=(int,)),
        Var("internal_p", read_pattern="^IN_PAR_06$", doc="The internal proportional."),
        Cmd(
            "set_internal_p",
            r"^OUT_PAR_06 ([0-9]*\.?[0-9]+)$",
            argument_mappings=(float,),
        ),
        Var("internal_i", read_pattern="^IN_PAR_07$", doc="The internal integral."),
        Cmd("set_internal_i", "^OUT_PAR_07 ([0-9]*)$", argument_mappings=(int,)),
        Var("internal_d", read_pattern="^IN_PAR_08$", doc="The internal derivative."),
        Cmd("set_internal_d", "^OUT_PAR_08 ([0-9]*)$", argument_mappings=(int,)),
        Var("external_p", read_pattern="^IN_PAR_09$", doc="The external proportional."),
        Cmd(
            "set_external_p",
            r"^OUT_PAR_09 ([0-9]*\.?[0-9]+)$",
            argument_mappings=(float,),
        ),
        Var("external_i", read_pattern="^IN_PAR_11$", doc="The external integral."),
        Cmd("set_external_i", "^OUT_PAR_11 ([0-9]*)$", argument_mappings=(int,)),
        Var("external_d", read_pattern="^IN_PAR_12$", doc="The external derivative."),
        Cmd("set_external_d", "^OUT_PAR_12 ([0-9]*)$", argument_mappings=(int,)),
    }

    in_terminator = "\r"
    out_terminator = "\n"  # Different from version 1
