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

"""
This file makes it more convenient for unit tests to import things
from the mock-package in a way that is compatible with Python 2 and 3.

Instead of the usual `from mock import Mock`, tests just need to specify
`from .mock import Mock` and the "import resolution" is handled there.
"""

from __future__ import absolute_import

try:
    from unittest.mock import *
except ImportError:
    from mock import *
