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

import importlib


class Adapter(object):
    protocol = None

    def __init__(self, device, arguments, bindings=None):
        self._device = device

    def process(self, cycle_delay=0.1):
        pass


def import_adapter(module_name, class_name=None):
    """
    This function imports an Adapter class from a module in the adapters package.
    It is equivalent to the following statement:

        from adapter.module_name import class_name

    But instead of importing class_name into the current namespace, the class
    is returned so that it can be used to instantiate objects. The usage would be:

        CommunicationAdapter = import_adapter('epics', 'EpicsAdapter')
        adapter = CommunicationAdapter()

    If class_name is omitted, the module will return the first subclass of Adapter
    it can find in the module. If no suitable class is found, an exception is raised.


    :param module_name: Submodule of 'adapters' from which to import the Adapter.
    :param class_name: Class name of the Adapter.
    :return: Adapter class.
    """
    module = importlib.import_module('.{}'.format(module_name), 'adapters')

    for module_member in dir(module):
        module_object = getattr(module, module_member)

        try:
            if issubclass(module_object, Adapter) and module_object != Adapter:
                if class_name is None or module_member == class_name:
                    return module_object
        except TypeError:
            pass

    raise RuntimeError('No suitable Adapter found in module \'{}\''.format(module_name))
