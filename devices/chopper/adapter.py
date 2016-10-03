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

from adapters.epics import EpicsAdapter, pv, cmd_pv


class ChopperEpicsAdapter(EpicsAdapter):
    pvs = [
        pv('Spd-RB', 'target_speed'),
        pv('Spd', 'target_speed'),
        pv('ActSpd', 'speed'),

        pv('Phs-RB', 'target_phase'),
        pv('Phs', 'target_phase'),
        pv('ActPhs', 'phase'),

        pv('ParkAng-RB', 'target_parking_position'),
        pv('ParkAng', 'target_parking_position'),
        pv('AutoPark', 'auto_park', type='enum', enums=['false', 'true']),
        pv('State', 'state', type='string'),

        cmd_pv('CmdS',
               commands={'start': 'start',
                         'stop': 'stop',
                         'set_phase': 'lock_phase',
                         'unlock': 'unlock',
                         'park': 'park',
                         'init': 'initialize',
                         'deinit': 'deinitialize'},
               buffer_pv='CmdL', type='string'),
        pv('CmdL', type='string'),
    ]
