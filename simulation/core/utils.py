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

def dict_strict_update(base_dict, update_dict):
    """
    This function updates base_dict with update_dict if and only if update_dict does not contain
    keys that are not already in base_dict. It is essentially a more strict interpretation of the
    term "updating" the dict.

    If update_dict contains keys that are not in base_dict, a RuntimeError is raised.

    :param base_dict: The dict that is to be updated. This dict is modified.
    :param update_dict: The dict containing the new values.
    """
    additional_keys = update_dict.viewkeys() - base_dict.viewkeys()
    if len(additional_keys) > 0:
        raise RuntimeError(
            'The update dictionary contains keys that are not part of the base dictionary: {}'.format(
                str(additional_keys)))

    base_dict.update(update_dict)
