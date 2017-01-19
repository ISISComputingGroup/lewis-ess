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
This module contains everything logging-related in Lewis. There is one relevant
module level variable that defines the default log format, ``default_log_format``.

All places that use logging in Lewis prefix their logger names with ``lewis`` so
that you can easily control the logs caused by Lewis if you use it as a library.
Lewis uses the default settings of the logging module, so if you use Lewis as a
library and do not have any logging enabled, messages that are more severe than ``WARNING``
are printed to stdout. For details on how to disable that behavior, change levels
for certain loggers and so on, please refer to the documentation
of the standard `logging`_ library.

.. _logging: https://docs.python.org/2/library/logging.html
"""

from __future__ import absolute_import
from six import string_types

import logging

root_logger_name = 'lewis'
default_log_format = '%(asctime)s %(levelname)s %(name)s: %(message)s'


class HasLog(object):
    """
    This is a mixin for enabling class-level logging.

    Inheriting from this mixin adds a ``log`` member to the class, which
    is an instance of ``logging.Logger``. The logger automatically get
    assigned a name that depends on the contents of the ``context`` parameter.

    In the default case, the name of the logger of class ``Foo`` is ``lewis.Foo``.
    This naming scheme works for many cases, but for classes that are used in
    different places, such as :class:`~lewis.core.statemachine.StateMachine`, it
    would not be clear where exactly the log message originated from. For these
    cases it is possible to supply a "context" for the log (which can also be set
    after construction using :meth:`_set_logging_context`).

    If ``context`` is a string, that string is directly inserted between ``lewis``
    and ``Foo``, so that the logger name would be ``lewis.bar.Foo`` if context
    was ``'bar'``. The more common case is probably ``context`` being an object of
    some class, in which case the class name is inserted. If ``context`` is an object
    of type ``Bar``, the logger name of ``Foo`` would be ``lewis.Bar.Foo``.

    To provide a more concrete example in terms of Lewis, this is used for the state
    machine logger in a device. So the logs of the state machine belonging to a certain
    device appear in the log as originating from ``lewis.DeviceName.StateMachine``, which
    makes it possible to distinguish between messages from different state machines.

    Example for how to use logging in a class:

    .. sourcecode:: Python

        from lewis.core.logging import HasLog

        class Foo(HasLog, OtherBase):
            def __init__(self):
                super(Foo, self).__init__()

            def bar(self, baz):
                self.log.debug('Called bar with parameter baz=%s', baz)
                return baz is not None

    :param context: Context to modify logger name. String or object, defaults to ``None``.

    .. seealso::

        Two central classes in Lewis inherit from this mixin, :class:`~lewis.adapters.Adapter`
        and :class:`~lewis.core.devices.DeviceBase`.

        :class:`~lewis.core.statemachine.StateMachine`, :class:`~lewis.core.statemachine.State`
        and :class:`~lewis.core.statemachine.Transition` also inherit from this, so logging under
        clearly defined names is automatically available in classes inheriting from those as well.
    """
    log = None
    _logger_name = None

    def __init__(self, context=None):
        super(HasLog, self).__init__()
        self._logger_name = self.__class__.__name__

        self.log = self.__get_logger(context)

    def _set_logging_context(self, context):
        """
        Changes the logger name of this class using the supplied context
        according to the rules described in the class documentation. To
        clear the context of a class logger, supply ``None`` as the argument.

        :param context: String or object, ``None`` to clear context.
        """
        self.log = self.__get_logger(context)

    def __get_logger(self, context):
        log_names = [root_logger_name, self._logger_name]

        if context is not None:
            log_names.insert(1,
                             context if isinstance(context,
                                                   string_types) else context.__class__.__name__)

        return logging.getLogger('.'.join(log_names))
