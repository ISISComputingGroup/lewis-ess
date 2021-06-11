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

from io import StringIO


def get_usage_text(parser, indent=None):
    """
    This small helper function extracts the help information from an ArgumentParser instance
    and indents the text by the number of spaces supplied in the indent-argument.

    :param parser: ArgumentParser object.
    :param indent: Number of spaces to put before each line or None.
    :return: Formatted help string of the supplied parser.
    """
    usage_text = StringIO()
    parser.print_help(usage_text)

    usage_string = usage_text.getvalue()

    if indent is None:
        return usage_string

    return "\n".join([" " * indent + line for line in usage_string.split("\n")])
