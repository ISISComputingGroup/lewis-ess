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


epics = {
    'Spd-RB': {'property': 'target_speed'},
    'ActSpd': {'property': 'speed'},
    'Spd': {'property': 'target_speed'},

    'Phs-RB': {'property': 'target_phase'},
    'ActPhs': {'property': 'phase'},
    'Phs': {'property': 'target_phase'},

    'ParkAng-RB': {'property': 'target_parking_position'},
    'ParkAng': {'property': 'target_parking_position'},
    'AutoPark': {'type': 'enum',
                 'enums': ['false', 'true'],
                 'property': 'auto_park'},

    'State': {'type': 'string', 'property': 'state'},

    'CmdS': {'type': 'string',
             'commands': {
                 'start': 'start',
                 'stop': 'stop',
                 'set_phase': 'lock_phase',
                 'unlock': 'unlock',
                 'park': 'park',
                 'init': 'initialize',
                 'deinit': 'deinitialize'
             },
             'buffer': 'CmdL'},

    'CmdL': {'type': 'string'}
}
