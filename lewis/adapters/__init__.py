# -*- coding: utf-8 -*-
# *********************************************************************
# lewis - a library for creating hardware device simulators
# Copyright (C) 2016-2017 European Spallation Source ERIC
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
This module defines a base class for adapters and some supporting infrastructure.
"""


class ForwardProperty(object):
    """
    This is a small helper class that can be used to act as
    a forwarding property to relay property setting/getting
    to a member of the class it's installed on.

    This is a small helper class that can be used to act as
    a forwarding property to relay property setting/getting
    to a member of the class it's installed on.

    Typical use would be:

    .. sourcecode:: Python

        a = Foo()
        a._b = Bar() # Bar has property baz

        type(a).forward = ForwardProperty('_b', 'baz')

        a.forward = 10 # equivalent to a._b.baz = 10

    Note that this modifies the type ``Foo``. Usage must thus be
    limited to cases where this type modification is
    acceptable.

    :param target_member: Target member to forward to.
    :param property_name: Property of target to access.
    :param instance: Object from which to obtain target_member for the purpose of extracting
                     the docstring of the property identified by property_name. If it doesn't
                     exist on the type, of target_member, the docstring is not copied.

    .. seealso:: See :class:`ForwardMethod` to forward method calls to another object.
    """

    def __init__(self, target_member, property_name, instance=None):
        self._target_member = target_member
        self._prop = property_name

        # Extract docstring from the property that's being forwarded.
        # The property exists in the type of the specified target_member of instance,
        # so getattr must be called on the type, not object, otherwise the
        # docstring of the returned value would be stored.
        self.__doc__ = getattr(type(getattr(instance, self._target_member)),
                               self._prop, None).__doc__

    def __get__(self, instance, instance_type=None):
        """
        This method forwards property read access on instance
        to the member of instance that was selected in __init__.

        :param instance: Instance of type.
        :param instance_type: Type.
        :return: Attribute value of member property.
        """
        if instance is not None:
            return getattr(getattr(instance, self._target_member), self._prop)

        return self

    def __set__(self, instance, value):
        """
        This method forwards property write access on instance
        to the member of instance that was selected in __init__.

        :param instance: Instance of type.
        :param value: Value of property.
        """

        setattr(getattr(instance, self._target_member), self._prop, value)
