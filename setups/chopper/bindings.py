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
    'Spd-RB': {'property': 'speed'},
    'ActSpd': {'property': 'speed'},
    'Spd': {'property': 'targetSpeed'},

    'Phs-RB': {'property': 'phase'},
    'ActPhs': {'property': 'phase'},
    'Phs': {'property': 'targetPhase'},

    'ParkAng-RB': {'property': 'parkingPosition'},
    'ParkAng': {'property': 'targetParkingPosition'},
    'AutoPark': {'type': 'enum',
                 'enums': ['false', 'true'],
                 'property': 'autoPark'},

    'State': {'type': 'string', 'property': 'state'},

    'CmdS': {'type': 'string',
             'commands': {
                 'start': 'start',
                 'stop': 'stop',
                 'set_phase': 'lockPhase',
                 'unlock': 'unlock',
                 'park': 'park',
                 'init': 'initialize',
                 'deinit': 'deinitialize'
             },
             'buffer': 'CmdL'},

    'CmdL': {'type': 'string'}
}
