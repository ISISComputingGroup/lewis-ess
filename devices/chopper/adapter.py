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
    pvs = {
        'Spd-RB': pv('target_speed', read_only=True),
        'Spd': pv('target_speed'),
        'ActSpd': pv('speed', read_only=True),

        'Phs-RB': pv('target_phase', read_only=True),
        'Phs': pv('target_phase'),
        'ActPhs': pv('phase', read_only=True),

        'ParkAng-RB': pv('target_parking_position', read_only=True),
        'ParkAng': pv('target_parking_position'),
        'AutoPark': pv('auto_park', type='enum', enums=['false', 'true']),
        'State': pv('state', read_only=True, type='string'),

        'CmdS': pv('execute_command', type='string'),
        'CmdL': pv('last_command', type='string', read_only=True),
    }

    _commands = {'start': 'start',
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
        command = self._commands.get(value)

        getattr(self._device, command)()
        self._last_command = command

    @property
    def last_command(self):
        return self._last_command
