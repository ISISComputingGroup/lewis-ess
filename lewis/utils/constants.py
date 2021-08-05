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
List of constants which are useful in communications
"""

# Single character constant
STX = chr(2)
ETX = chr(3)
EOT = chr(4)
ENQ = chr(5)
ACK = chr(6)

# A dictionary of constants this is useful in e.g. "{STX} message{ETX}".format(**COMMAND_CHARS)
ASCII_CHARS = {"STX": STX, "ACK": ACK, "EOT": EOT, "ENQ": ENQ, "ETX": ETX}
