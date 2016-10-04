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

from adapters.epics import EpicsAdapter, pv


class ChopperEpicsAdapter(EpicsAdapter):
    pvs = [
        pv('Spd-RB', 'target_speed', read_only=True),
        pv('Spd', 'target_speed'),
        pv('ActSpd', 'speed', read_only=True),

        pv('Phs-RB', 'target_phase', read_only=True),
        pv('Phs', 'target_phase'),
        pv('ActPhs', 'phase', read_only=True),

        pv('ParkAng-RB', 'target_parking_position', read_only=True),
        pv('ParkAng', 'target_parking_position'),
        pv('AutoPark', 'auto_park', type='enum', enums=['false', 'true']),
        pv('State', 'state', read_only=True, type='string'),

        pv('CmdS', 'execute_command', type='string'),
        pv('CmdL', 'last_command', type='string', read_only=True),
    ]

    commands = {'start': 'start',
                'stop': 'stop',
                'set_phase': 'lock_phase',
                'unlock': 'unlock',
                'park': 'park',
                'init': 'initialize',
                'deinit': 'deinitialize'}

    _last_command = ''

    @property
    def execute_command(self):
        return ''

    @execute_command.setter
    def execute_command(self, value):
        command = self.commands.get(value)

        getattr(self._target, command)()
        self._last_command = command

    @property
    def last_command(self):
        return self._last_command
