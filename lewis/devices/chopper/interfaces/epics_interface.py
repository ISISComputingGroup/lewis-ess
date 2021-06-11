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


class ChopperEpicsInterface(EpicsInterface):
    """
    ESS chopper EPICS interface

    Interaction with this interface should happen via ChannelAccess (CA). The PV-names
    usually carry a prefix which depends on the concrete device and environment, so
    it is omitted in this description. The dynamically generated description of the PVs
    does however contain the prefix so that the names can be copy-pasted easily.

    The first step is to initialize the chopper, for example via caput on the command line:

        $ caput CmdS init

    After this, the chopper is in a state where it can be started:

        $ caget State
        State                          stopped

    To set a specific speed and phase, the setpoints have to be configured via caput:

        $ caput Spd 100
        $ caput Phs 34.5

    Then the chopper can be commanded to move towards those values:

        $ caput CmdS start

    Now the disc accelerates to the setpoints, the state should now be different:

        $ caget State
        State                          accelerating

    The possible commands are part of the PV-specific documentation.
    """

    pvs = {
        "Spd-RB": PV(
            "target_speed",
            read_only=True,
            doc="Readback value of the speed setpoint in Hz.",
        ),
        "Spd": PV("target_speed", doc="Speed setpoint in Hz."),
        "ActSpd": PV(
            "speed",
            read_only=True,
            doc="Current rotation speed of the chopper disc in Hz.",
        ),
        "Phs-RB": PV(
            "target_phase",
            read_only=True,
            doc="Readback value of phase setpoint in degrees.",
        ),
        "Phs": PV("target_phase", doc="Phase setpoint in degrees."),
        "ActPhs": PV(
            "phase", read_only=True, doc="Current phase of the chopper disc in degrees."
        ),
        "ParkAng-RB": PV(
            "target_parking_position",
            read_only=True,
            doc="Readback value of the discs parking position setpoint in degrees.",
        ),
        "ParkAng": PV(
            "target_parking_position",
            doc="The discs parking position setpoint in degrees.",
        ),
        "AutoPark": PV(
            "auto_park",
            doc="If enabled, the chopper disc will be moved to the parking "
            "position automatically when the speed is 0 or the chopper "
            "is otherwise stopped. 0 means False, 1 means True, the string "
            'representations of the enum values are "false" and "true".',
            type="enum",
            enums=["false", "true"],
        ),
        "State": PV("state", read_only=True, type="string"),
        "CmdS": PV("execute_command", type="string"),
        "CmdL": PV("last_command", type="string", read_only=True),
    }

    _commands = {
        "start": "start",
        "stop": "stop",
        "set_phase": "lock_phase",
        "unlock": "unlock",
        "park": "park",
        "init": "initialize",
        "deinit": "deinitialize",
    }

    _last_command = ""

    @property
    def execute_command(self):
        """
        Command to execute. Possible commands are start, stop, set_phase,
        unlock, park, init, deinit.
        """
        return ""

    @execute_command.setter
    def execute_command(self, value):
        command = self._commands.get(value)

        getattr(self.device, command)()
        self._last_command = command

    @property
    def last_command(self):
        """
        The last command that was executed successfully.
        """
        return self._last_command
