# -*- coding: utf-8 -*-
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
This module contains some useful helper classes and functions that are not specific to a certain
module contained in the Core API.
"""

from __future__ import absolute_import
from six import string_types

import imp
import importlib
import textwrap
import inspect
from datetime import datetime

import os.path as osp
from os import listdir

from .exceptions import PlanktonException, LimitViolationException


def get_available_submodules(package):
    """
    This function returns a list of available submodules in a package.

    :param package: Name of the package.
    :return: Available submodules in package.
    """

    module = importlib.import_module(package)
    path = module.__path__[0]

    submodule_candidates = [extract_module_name(osp.join(path, entry)) for entry in listdir(path)]

    return [submodule for submodule in submodule_candidates if is_module(submodule, [path])]


def extract_module_name(absolute_path):
    """
    This function tries to extract a valid module name from the basename of the supplied path.
    If it's a directory, the directory name is returned, if it's a file, the file name
    without extension is returned. If the basename starts with _ or it's a file with an
    ending different from .py, the function returns None

    :param absolute_path: Absolute path of something that might be a module.
    :return: Module name or None.
    """
    base_name = osp.basename(osp.normpath(absolute_path))

    # If the basename starts with _ it's probably __init__.py or __pycache__ or something internal.
    # At the moment there seems to be no use case for those
    if base_name.startswith('_'):
        return None

    # If it's a directory, there's nothing else to check, so it can be returned directly
    if osp.isdir(absolute_path):
        return base_name

    module_name, extension = osp.splitext(base_name)

    # If it's a file, it must have a .py ending
    if extension == '.py':
        return module_name

    return None


def is_module(module, paths):
    """
    Small helper function that returns True if module is a sub-module in package.

    :param module: Name of the sub-module to check.
    :param paths: List of paths where the module is located.
    :return: True if module is a sub-module of package.
    """
    try:
        imp.find_module(module, paths)
        return True
    except (ImportError, TypeError):
        return False


def dict_strict_update(base_dict, update_dict):
    """
    This function updates base_dict with update_dict if and only if update_dict does not contain
    keys that are not already in base_dict. It is essentially a more strict interpretation of the
    term "updating" the dict.

    If update_dict contains keys that are not in base_dict, a RuntimeError is raised.

    :param base_dict: The dict that is to be updated. This dict is modified.
    :param update_dict: The dict containing the new values.
    """
    additional_keys = set(update_dict.keys()) - set(base_dict.keys())
    if len(additional_keys) > 0:
        raise RuntimeError(
            'The update dictionary contains keys that are not part of '
            'the base dictionary: {}'.format(str(additional_keys)))

    base_dict.update(update_dict)


def seconds_since(start):
    """
    This is a small helper function that returns the elapsed seconds
    since start using datetime.datetime.now().

    :param start: Start time.
    :return: Elapsed seconds since start time.
    """
    return (datetime.now() - start).total_seconds()


class FromOptionalDependency(object):
    """
    This is a utility class for importing classes from a module or
    replacing them with dummy types if the module can not be loaded.

    Assume module 'a' that does:

    .. sourcecode:: Python

        from b import C, D

    and module 'e' which does:

    .. sourcecode:: Python

        from a import F

    where 'b' is a hard to install dependency which is thus optional.
    To still be able to do:

    .. sourcecode:: Python

        import e

    without raising an error, for example for inspection purposes,
    this class can be used as a workaround in module 'a':

    .. sourcecode:: Python

        C, D = FromOptionalDependency('b').do_import('C', 'D')

    which is not as pretty as the actual syntax, but at least it
    can be read in a similar way. If the module 'b' can not be imported,
    stub-types are created that are called 'C' and 'D'. Everything depending
    on these types will work until any of those are instantiated - in that
    case an exception is raised.

    The exception can be controlled via the exception-parameter. If it is a
    string, a PlanktonException is constructed from it. Alternatively it can
    be an instance of an exception-type. If not provided, a PlanktonException
    with a standard message is constructed. If it is anything else, a RuntimeError
    is raised.

    Essentially, this class helps deferring ImportErrors until anything from
    the module that was attempted to load is actually used.

    :param module: Module from that symbols should be imported.
    :param exception: Text for PlanktonException or custom exception object.
    """

    def __init__(self, module, exception=None):
        self._module = module

        if exception is None:
            exception = 'The optional dependency \'{}\' is required for the ' \
                        'functionality you tried to use.'.format(self._module)

        if isinstance(exception, string_types):
            exception = PlanktonException(exception)

        if not isinstance(exception, BaseException):
            raise RuntimeError(
                'The exception parameter has to be either a string or a an instance of an '
                'exception type (derived from BaseException).')

        self._exception = exception

    def do_import(self, *names):
        """
        Tries to import names from the module specified on initialization
        of the FromOptionalDependency-object. In case an ImportError occurs,
        the requested names are replaced with stub objects.

        :param names: List of strings that are used as type names.
        :return: Tuple of actual symbols or stub types with provided names. If there is only one
                 element in the tuple, that element is returned.
        """
        try:
            module_object = importlib.import_module(self._module)

            objects = tuple(getattr(module_object, name) for name in names)
        except ImportError:
            def failing_init(obj, *args, **kwargs):
                raise self._exception

            objects = tuple(type(name, (object,), {'__init__': failing_init})
                            for name in names)

        return objects if len(objects) != 1 else objects[0]


def format_doc_text(text):
    """
    A very thin wrapper around textwrap.fill to consistently wrap documentation text
    for display in a command line environment. The text is wrapped to 99 characters with an
    indentation depth of 4 spaces. Each line is wrapped independently in order to preserve
    manually added line breaks.

    :param text: The text to format, it is cleaned by inspect.cleandoc.
    :return: The formatted doc text.
    """

    return '\n'.join(
        textwrap.fill(line, width=99, initial_indent='    ', subsequent_indent='    ')
        for line in inspect.cleandoc(text).splitlines())


class check_limits(object):
    """
    This decorator helps to make sure that the parameter of a property setter (or any other
    method with one argument) is within certain numerical limits.

    It's possible to set static limits using floats or ints:

    ..sourcecode:: Python

        class Foo(object):
            _bar = 0

            @property
            def bar(self):
                return self._bar

            @bar.setter
            @check_limits(0, 15)
            def bar(self, new_value):
                self._bar = new_value

    But sometimes this is not flexible enough, so it's also possible to supply strings, which
    are the names of attributes of the object the decorated method belongs with:

    .. sourcecode:: Python

        class Foo(object):
            _bar = 0

            bar_min = 0
            bar_max = 24

            @property
            def bar(self):
                return self._bar

            @bar.setter
            @check_limits('bar_min', 'bar_max')
            def bar(self, new_value):
                self._bar = new_value

    This will make sure that the new value is always between ``bar_min`` and ``bar_max``, even
    if they change at runtime.

    If the value is outside the specified limits, an exception of the type
    :class:`~plankton.core.exceptions.LimitViolationException` is raised.

    :param low_limit: Numerical lower limit or name of attribute that contains limit.
    :param high_limit: Numerical upper limit or name of attribute that contains limit.
    """

    def __init__(self, low_limit, high_limit):
        self._lower = low_limit
        self._upper = high_limit

    def __call__(self, f):
        def limit_checked(obj, new_value):
            low = getattr(obj, self._lower) if isinstance(self._lower,
                                                          string_types) else self._lower
            high = getattr(obj, self._upper) if isinstance(self._upper,
                                                           string_types) else self._upper

            if not (low <= new_value <= high):
                raise LimitViolationException(
                    '%f is outside limits (%f, %f)' % (new_value, low, high))

            return f(obj, new_value)

        return limit_checked
