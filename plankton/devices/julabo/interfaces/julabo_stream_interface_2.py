# -*- coding: utf-8 -*-
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

from plankton.adapters.stream import StreamAdapter, Cmd


class JulaboStreamInterfaceV2(StreamAdapter):
    """Julabos can have different commands sets depending on the version number of the hardware.

    This protocol matches that for: FP50-HE (untested.
    """

    protocol = "julabo-version-2"

    commands = {
        Cmd('get_bath_temperature', '^IN_PV_00$'),
        Cmd('get_external_temperature', '^IN_PV_01$'),
        Cmd('get_power', '^IN_PV_02$'),
        Cmd('get_set_point', '^IN_SP_00$'),
        Cmd('get_high_limit', '^IN_SP_03$'),    # Different from version 1
        Cmd('get_low_limit', '^IN_SP_04$'),     # Different from version 1
        Cmd('get_circulating', '^IN_MODE_05$'),
        Cmd('get_version', '^VERSION$'),
        Cmd('get_status', '^STATUS$'),
        Cmd('set_set_point', '^OUT_SP_00 ([0-9]*\.?[0-9]+)$'),
        Cmd('set_mode', '^OUT_MODE_05 [0|1]{1}$'),
        Cmd('get_internal_p', '^IN_PAR_06$'),
        Cmd('get_internal_i', '^IN_PAR_07$'),
        Cmd('get_internal_d', '^IN_PAR_08$'),
        Cmd('set_internal_p', '^OUT_PAR_06 ([0-9]*\.?[0-9]+)$'),
        Cmd('set_internal_i', '^OUT_PAR_07 ([0-9]*)$'),
        Cmd('set_internal_d', '^OUT_PAR_08 ([0-9]*)$'),
        Cmd('get_external_p', '^IN_PAR_09$'),
        Cmd('get_external_i', '^IN_PAR_11$'),
        Cmd('get_external_d', '^IN_PAR_12$'),
        Cmd('set_external_p', '^OUT_PAR_09 ([0-9]*\.?[0-9]+)$'),
        Cmd('set_external_i', '^OUT_PAR_11 ([0-9]*)$'),
        Cmd('set_external_d', '^OUT_PAR_12 ([0-9]*)$'),
    }

    in_terminator = '\r'
    out_terminator = '\n'   # Different from version 1


