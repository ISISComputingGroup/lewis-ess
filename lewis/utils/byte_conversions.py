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

import struct

BYTE = 2 ** 8


def _get_byteorder_name(low_byte_first):
    """
    Get the python name for low byte first
    :param low_byte_first: True for low byte first; False for MSB first
    :return: name
    """
    return "little" if low_byte_first else "big"


def int_to_raw_bytes(integer, length, low_byte_first) -> bytes:
    """
    Converts an integer to an unsigned set of bytes with the specified length (represented as a string). Unless the
    integer is negative in which case it converts to a signed integer.

    If low byte first is True, the least significant byte comes first, otherwise the most significant byte comes first.

    :param integer: The integer to convert.
    :param length: The length of the result.
    :param low_byte_first: Whether to put the least significant byte first.

    :return: string representation of the bytes.
    """
    return integer.to_bytes(
        length=length, byteorder=_get_byteorder_name(low_byte_first), signed=integer < 0
    )


def raw_bytes_to_int(raw_bytes, low_bytes_first=True):
    """
    Converts an unsigned set of bytes to an integer.

    :param raw_bytes: A string representation of the raw bytes.
    :param low_bytes_first: Whether the given raw bytes are in little endian or not. True by default.

    :return: The integer represented by the raw bytes passed in.
    """
    return int.from_bytes(raw_bytes, byteorder=_get_byteorder_name(low_bytes_first))


def float_to_raw_bytes(real_number: float, low_byte_first: bool = True) -> bytes:
    """
    Converts an floating point number to an unsigned set of bytes.

    :param real_number: The float to convert.
    :param low_byte_first: Whether to put the least significant byte first. True by default.

    :return: A string representation of the bytes.
    """
    raw_bytes = bytes(struct.pack(">f", real_number))

    return raw_bytes[::-1] if low_byte_first else raw_bytes


def raw_bytes_to_float(raw_bytes):
    """
    Convert a set of bytes to a floating point number

    :param raw_bytes: A string representation of the raw bytes.

    :return: float: The floating point number represented by the given bytes.
    """
    return struct.unpack("f", raw_bytes[::-1])[0]
