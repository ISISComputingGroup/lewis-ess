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
    def __init__(self, *args, **kwargs):
        pass

    def run(self, target):
        pass


def import_adapter(module_name):
    module = importlib.import_module('.{}'.format(module_name), 'adapters')

    for module_member in dir(module):
        module_object = getattr(module, module_member)

        try:
            if issubclass(module_object, Adapter) and module_object != Adapter:
                return module_object
        except TypeError:
            pass

    raise RuntimeError('No suitable Adapter found in module \'{}\''.format(module_name))
