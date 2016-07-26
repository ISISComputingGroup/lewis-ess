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

from collections import OrderedDict

from core import StateMachine, CanProcessComposite, Context
from core.utils import dict_strict_update

from defaults import *


class LinkamT95Context(Context):
    def initialize(self):
        self.start_commanded = False
        self.stop_commanded = False

        self.pump_speed = 0
        self.temperature = 0.0

        self.pump_manual_mode = False
        self.manual_target_speed = 0


class SimulatedLinkamT95(CanProcessComposite, object):
    def __init__(self, override_states=None, override_transitions=None):
        super(SimulatedLinkamT95, self).__init__()

        self._context = LinkamT95Context()

        state_handlers = {
            'stopped': DefaultStoppedState(),
            'started': DefaultStartedState(),
            'heat': DefaultHeatState(),
            'hold': DefaultHoldState(),
            'cool': DefaultCoolState(),
        }

        if override_states is not None:
            dict_strict_update(state_handlers, override_states)

        transition_handlers = OrderedDict([
            (('stopped', 'started'), lambda: self._context.start_commanded),

            (('started', 'stopped'), lambda: self._context.stop_commanded),
            (('started', 'heat'), lambda: False),
            (('started', 'hold'), lambda: False),
            (('started', 'cool'), lambda: False),

            (('heat', 'hold'), lambda: False),
            (('heat', 'cool'), lambda: False),
            (('heat', 'stopped'), lambda: self._context.stop_commanded),

            (('hold', 'heat'), lambda: False),
            (('hold', 'cool'), lambda: False),
            (('hold', 'stopped'), lambda: self._context.stop_commanded),

            (('cool', 'heat'), lambda: False),
            (('cool', 'hold'), lambda: False),
            (('cool', 'stopped'), lambda: self._context.stop_commanded),
        ])

        if override_transitions is not None:
            dict_strict_update(transition_handlers, override_transitions)

        self._csm = StateMachine({
            'initial': 'stopped',
            'states': state_handlers,
            'transitions': transition_handlers,
        }, context=self._context)

        self.addProcessor(self._csm)

    def getStatus(self):
        return "0123456789\n" + self._csm.state + "\n"

    def setRate(self, param):
        pass

    def setLimit(self, param):
        pass

    def start(self):
        self._context.start_commanded = True

    def stop(self):
        self._context.stop_commanded = True

    def hold(self):
        pass

    def heat(self):
        pass

    def cool(self):
        pass

    def pumpCommand(self, param):
        pass
