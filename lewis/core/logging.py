# -*- coding: utf-8 -*-
# *********************************************************************
# lewis - a library for creating hardware device simulators
# Copyright (C) 2016-2021 European Spallation Source ERIC
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

import logging

root_logger_name = "lewis"
default_log_format = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def has_log(target):
    """
    This is a decorator to add logging functionality to a class or function.

    Applying this decorator to a class or function will add two new members:

     - ``log`` is an instance of ``logging.Logger``. The name of the logger is
       set to ``lewis.Foo`` for a class named Foo.
     - ``_set_logging_context`` is a method that modifies the name of the logger
       when the class is used in a certain context.

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

        from lewis.core.logging import has_log

        @has_log
        class Foo(Base):
            def __init__(self):
                super(Foo, self).__init__()

            def bar(self, baz):
                self.log.debug('Called bar with parameter baz=%s', baz)
                return baz is not None

    It works similarly for free functions, although the actual logging calls are a bit different:

    .. sourcecode:: Python

        from lewis.core.logging import has_log

        @has_log
        def foo(bar):
            foo.log.info('Called with argument bar=%s', bar)
            return bar

    The name of the logger is ``lewis.foo``, the context could also be modified by calling
    ``foo._set_logging_context``.

    :param target: Target to decorate with logging functionality.
    """
    logger_name = target.__name__

    def get_logger_name(context=None):
        log_names = [root_logger_name, logger_name]

        if context is not None:
            log_names.insert(
                1, context if isinstance(context, str) else context.__class__.__name__
            )

        return ".".join(log_names)

    def _set_logging_context(obj, context):
        """
        Changes the logger name of this class using the supplied context
        according to the rules described in the documentation of :func:`has_log`. To
        clear the context of a class logger, supply ``None`` as the argument.

        :param context: String or object, ``None`` to clear context.
        """
        obj.log.name = get_logger_name(context)

    target.log = logging.getLogger(get_logger_name())
    target._set_logging_context = _set_logging_context

    return target
