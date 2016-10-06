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

from __future__ import print_function
from six import iteritems

from argparse import ArgumentParser

from pcaspy import Driver, SimpleServer

from adapters import Adapter
from core.utils import seconds_since
from datetime import datetime


class pv(object):
    def __init__(self, target_property, poll_interval=1.0, read_only=False, **kwargs):
        self.property = target_property
        self.read_only = read_only
        self.poll_interval = poll_interval
        self.config = kwargs


class PropertyExposingDriver(Driver):
    def __init__(self, target, pv_dict):
        super(PropertyExposingDriver, self).__init__()

        self._target = target
        self._pv_dict = pv_dict
        self._timers = {k: 0.0 for k in self._pv_dict.keys()}

    def write(self, pv, value):
        pv_object = self._pv_dict.get(pv)

        if not pv_object or pv_object.read_only:
            return False

        setattr(self._target, pv_object.property, value)

        self.setParam(pv, getattr(self._target, pv_object.property))

        return True

    def process_pv_updates(self, dt):
        # Updates bound parameters as needed
        for pv, pv_object in iteritems(self._pv_dict):
            self._timers[pv] += dt
            if self._timers[pv] >= pv_object.poll_interval:
                try:
                    self.setParam(pv, getattr(self._target, pv_object.property))
                    self._timers[pv] = 0.0
                except (AttributeError, TypeError):
                    pass

        self.updatePVs()


class ForwardProperty(object):
    def __init__(self, target_member, property_name):
        """
        This is a small helper class that can be used to act as
        a forwarding property to relay property setting/getting
        to a member of the class it's installed on.

        Typical use would be:

            a = Foo()
            a._b = Bar() # Bar has property baz

            type(a).forward = ForwardProperty('_b', 'baz')

            a.forward = 10 # equivalent to a._b.baz = 10

        Note that this modifies the type Baz. Usage must thus be
        limited to cases where this type modification is
        acceptable.

        :param target_member: Target member to forward to.
        :param prop: Property of target to access.
        """
        self._target_member = target_member
        self._prop = property_name

    def __get__(self, instance, type=None):
        """
        This method forwards property read access on instance
        to the member of instance that was selected in __init__.

        :param instance: Instance of type.
        :param type: Type.
        :return: Attribute value of member property.
        """
        return getattr(getattr(instance, self._target_member), self._prop)

    def __set__(self, instance, value):
        """
        This method forwards property write access on instance
        to the member of instance that was selected in __init__.

        :param instance: Instance of type.
        :param value: Type.
        """
        setattr(getattr(instance, self._target_member), self._prop, value)


class EpicsAdapter(Adapter):
    protocol = 'epics'
    pvs = None

    def __init__(self, device, arguments):
        super(EpicsAdapter, self).__init__(device, arguments)

        self._options = self._parseArguments(arguments)

        self._create_properties(self.pvs.values())

        self._server = SimpleServer()
        self._server.createPV(prefix=self._options.prefix,
                              pvdb={k: v.config for k, v in self.pvs.items()})
        self._driver = PropertyExposingDriver(target=self, pv_dict=self.pvs)

        self._last_update = datetime.now()

    def _create_properties(self, pvs):
        for pv in pvs:
            prop = pv.property

            if not prop in dir(self):
                if not prop in dir(self._device):
                    raise AttributeError('Can not find property \'' + prop + '\' in device or adapter.')
                setattr(type(self), prop, ForwardProperty('_device', prop))

    def _parseArguments(self, arguments):
        parser = ArgumentParser(description="Adapter to expose a device via EPICS")
        parser.add_argument('-p', '--prefix', help='Prefix to use for all PVs', default='')
        return parser.parse_args(arguments)

    def handle(self, cycle_delay=0.1):
        # pcaspy's process() is weird. Docs claim argument is "processing time" in seconds.
        # But this is not at all consistent with the calculated delta.
        # Having "watch caget" running has a huge effect too (runs faster when watching!)
        # Additionally, if you don't call it every ~0.05s or less, PVs stop working. Annoying.
        # Set it to 0.0 for maximum cycle speed.
        self._server.process(cycle_delay)
        self._driver.process_pv_updates(seconds_since(self._last_update))
        self._last_update = datetime.now()
