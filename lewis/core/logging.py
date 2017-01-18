# -*- coding: utf-8 -*-
# *********************************************************************
# lewis - a library for creating hardware device simulators
# Copyright (C) 2017 European Spallation Source ERIC
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
Logging stuff
"""

from __future__ import absolute_import
from six import string_types

import logging
import functools


class HasLog(object):
    def __init__(self, log=None):
        super(HasLog, self).__init__()
        self.logger_name = self.__class__.__name__

        self.attach_log(log if log is not None else self.__class__.__name__)

    def attach_log(self, log):
        if log is not None:
            extension = log if isinstance(log, string_types) else log.__class__.__name__

            self.log = logging.getLogger('.'.join((extension, self.logger_name)))
