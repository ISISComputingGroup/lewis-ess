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

import imp
import os.path as osp
from datetime import datetime
from os import listdir


def get_available_submodules(package, search_path=None):
    """
    This function returns a list of available submodules in a package.

    :param package: Name of the package.
    :param search_path: List of paths to search for package or None. Passed to imp.find_module
    :return: Available submodules in package.
    """
    file_name, path, descriptor = imp.find_module(package, search_path)

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

    # If it's a directory, there's nothing else to check, so it can be returned directly as the name
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
    :param path: List of paths where the module is located.
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
            'The update dictionary contains keys that are not part of the base dictionary: {}'.format(
                str(additional_keys)))

    base_dict.update(update_dict)


def seconds_since(start):
    return (datetime.now() - start).total_seconds()