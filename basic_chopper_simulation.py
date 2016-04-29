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

from adapters import run_pcaspy_server
from simulation import SimulatedChopper

prefix = 'SIM:'
pvdb = {
    'SPEED': {'property': 'speed'},
    'SPEED:SP': {'property': 'targetSpeed'},

    'PHASE': {'property': 'phase'},
    'PHASE:SP': {'property': 'targetPhase'},

    'PARKPOSITION': {'property': 'parkingPosition'},
    'PARKPOSITION:SP': {'property': 'targetParkingPosition'},

    'STATE': {'type': 'string', 'property': 'state'},

    'COMMAND': {'type': 'string',
                'commands': {
                    'START': 'start',
                    'STOP': 'stop',
                    'PHASE': 'lockPhase',
                    'COAST': 'unlock',
                    'PARK': 'park',
                    'INTERLOCK': 'interlock',
                    'RELEASE': 'release'
                },
                'buffer': 'LAST_COMMAND'},

    'LAST_COMMAND': {'type': 'string'}
}

chopper = SimulatedChopper()

# Run this in terminal window to monitor device:
#   watch -n 0.1 caget SIM:STATE SIM:LAST_COMMAND SIM:SPEED SIM:SPEED:SP SIM:PHASE SIM:PHASE:SP SIM:PARKPOSITION SIM:PARKPOSITION:SP
run_pcaspy_server(chopper, prefix, pvdb)
