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

root_logger_name = 'lewis'
root_logger = logging.getLogger(root_logger_name)


class HasLog(object):
    log = None
    _logger_name = None

    def __init__(self, log=None):
        super(HasLog, self).__init__()
        self._logger_name = self.__class__.__name__

        self.log = self._get_logger(log)

    def _set_logging_context(self, context):
        self.log = self._get_logger(context)

    def _get_logger(self, context):
        log_names = [root_logger_name, self._logger_name]

        if context is not None:
            log_names.insert(1, context if isinstance(context,
                                                      string_types) else context.__class__.__name__)

        return logging.getLogger('.'.join(log_names))
