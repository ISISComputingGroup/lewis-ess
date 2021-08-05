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
This module defines two classes related to one of lewis' essential concepts, namely
the cycle-based approach. :class:`CanProcess` and :class:`CanProcessComposite` implement the
composite design pattern so that it's possible to form a tree of objects which can perform
calculations based on an elapsed time Δt.
"""


class CanProcess:
    """
    The CanProcess class is meant as a base for all things that
    are able to process on the basis of a time delta (dt).

    The base implementation does nothing.

    There are three methods that can be implemented by sub-classes and are called in the
    process-method in this order:

        1. doBeforeProcess
        2. doProcess
        3. doAfterProcess

    The doBefore- and doAfterProcess methods are only called if a doProcess-method exists.
    """

    def __init__(self):
        super(CanProcess, self).__init__()

    def __call__(self, dt=0):
        self.process(dt)

    def process(self, dt=0):
        if hasattr(self, "doProcess"):
            if hasattr(self, "doBeforeProcess"):
                self.doBeforeProcess(dt)

            self.doProcess(dt)

            if hasattr(self, "doAfterProcess"):
                self.doAfterProcess(dt)


class CanProcessComposite(CanProcess):
    """
    This subclass of CanProcess is a convenient way of collecting
    multiple items that implement the CanProcess interface.

    Items can be added to the composite like this:

    .. sourcecode:: Python

        composite = CanProcessComposite()
        composite.add_processor(item_that_implements_CanProcess)

    The process-method calls the process-method of each contained
    item. Specific things that have to be done before or after the
    containing items are processed can be implemented in the doBefore-
    and doAfterProcess methods.
    """

    def __init__(self, iterable=()):
        super(CanProcessComposite, self).__init__()

        self._processors = []

        for item in iterable:
            self.add_processor(item)

    def add_processor(self, other):
        if isinstance(other, CanProcess):
            self._append_processor(other)

    def _append_processor(self, processor):
        self._processors.append(processor)

    def doProcess(self, dt):
        for processor in self._processors:
            processor.process(dt)
