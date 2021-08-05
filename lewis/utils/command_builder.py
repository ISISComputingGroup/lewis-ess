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
A fluent command builder for lewis.
"""

import re
from functools import partial

from lewis.adapters.stream import Cmd, regex
from lewis.utils.constants import ACK, ENQ, EOT, ETX, STX

string_arg = partial(str, encoding="utf-8")


class CmdBuilder(object):
    """
    Build a command for the stream adapter.

    Do this by creating this object, adding the values and then building it (this uses a fluent interface).

    For example to read a pressure the ioc might send "pres?" and when that happens this should call get_pres
    command would be:
    >>> CmdBuilder("get_pres").escape("pres?").build()
    This will generate the regex needed by Lewis. The escape is just making sure none of the characters are special
    reg ex characters.
    If you wanted to set a pressure the ioc might send "pres <pressure>" where <pressure> is a floating point number,
    the interface should call set_pres with that number. Now use:
    >>> CmdBuilder("set_pres").escape("pres ").float().build()
    this add float as a regularly expression capture group for your argument. It is equivalent to:
    >>> Cmd("set_pres", "pres ([+-]?\\d+\\.?\\d*)")
    There are various arguments like int and digit. Finally some special characters are included so if your protocol
    uses enquirey character ascii 5 you can match is using
    >>> CmdBuilder("set_pres").escape("pres?").enq().build()
    """

    def __init__(self, target_method, arg_sep="", ignore="", ignore_case=False):
        """
        Create a builder. Use build to create the final object

        :param target_method: name of the method target to call when the reg ex matches
        :param arg_sep: separators between arguments which are next to each other
        :param ignore: set of characters to ignore between text and arguments
        :param ignore_case: ignore the case when matching command
        """
        self._target_method = target_method
        self._arg_sep = arg_sep
        self._current_sep = ""
        self.argument_mappings = []
        if ignore is None or ignore == "":
            self._ignore = ""
        else:
            self._ignore = "[{0}]*".format(ignore)
        self._reg_ex = self._ignore

        self._ignore_case = ignore_case

    def _add_to_regex(self, regex, is_arg):
        self._reg_ex += regex + self._ignore
        if not is_arg:
            self._current_sep = ""

    def optional(self, text):
        """
        Add some escaped text which does not necessarily need to be there. For commands with optional parameters
        :param text: Text to add
        :return: builder
        """
        self._add_to_regex("(?:" + re.escape(text) + ")?", False)
        return self

    def escape(self, text):
        """
        Add some text to the regex which is escaped.

        :param text: text to add
        :return: builder
        """
        self._add_to_regex(re.escape(text), False)
        return self

    def regex(self, regex):
        """
        Add a regex to match but not as an argument.

        :param regex: regex to add
        :return: builder
        """
        self._add_to_regex(regex, False)
        return self

    def enum(self, *allowed_values):
        """
        Matches one of a set of specified strings.

        :param allowed_values: the values this function is allowed to match
        :return: builder
        """
        self._add_to_regex(
            "({})".format("|".join([re.escape(arg) for arg in allowed_values])),
            is_arg=True,
        )
        self.argument_mappings.append(string_arg)
        return self

    def spaces(self, at_least_one=False):
        """
        Add a regex for any number of spaces

        :param at_least_one: true there must be at least one space; false there can be any number including zero
        :return: builder

        """
        wildcard = "+" if at_least_one else "*"

        self._add_to_regex(" " + wildcard, False)
        return self

    def arg(self, arg_regex, argument_mapping=string_arg):
        """
        Add an argument to the command.

        :param arg_regex: regex for the argument (capture group will be added)
        :param argument_mapping: the type mapping for the argument (default is str)
        :return: builder
        """
        self._add_to_regex(self._current_sep + "(" + arg_regex + ")", True)
        self._current_sep = self._arg_sep
        self.argument_mappings.append(argument_mapping)
        return self

    def string(self, length=None):
        """
        Add an argument which is a string of a given length (if blank string is any length)

        :param length: length of string; None for any length
        :return: builder
        """
        if length is None:
            self.arg(".+")
        else:
            self.arg(".{{{}}}".format(length))
        return self

    def float(self, mapping=float, ignore=False):
        """
        Add a float argument.

        :param mapping: The type to cast the response to (default: float)
        :param ignore: True to match with a float but ignore the returned value (default: False)
        :return: builder
        """
        regex = r"[+-]?\d+\.?\d*"
        return self.regex(regex) if ignore else self.arg(regex, mapping)

    def digit(self, mapping=int, ignore=False):
        """
        Add a single digit argument.

        :param mapping: The type to cast the response to (default: int)
        :param ignore: True to match with a digit but ignore the returned value (default: False)
        :return: builder
        """
        return self.regex(r"\d") if ignore else self.arg(r"\d", mapping)

    def char(self, not_chars=None, ignore=False):
        """
        Add a single character argument.

        :param not_chars: characters that the character can not be; None for can be anything
        :param ignore: True to match with a char but ignore the returned value (default: False)
        :return: builder
        """
        regex = r"." if not_chars is None else "[^{}]".format("".join(not_chars))
        return self.regex(regex) if ignore else self.arg(regex)

    def int(self, mapping=int, ignore=False):
        """
        Add an integer argument.

        :param mapping: The type to cast the response to (default: int)
        :param ignore: True to match with a int but ignore the returned value (default: False)
        :return:  builder
        """
        regex = r"[+-]?\d+"
        return self.regex(regex) if ignore else self.arg(regex, mapping)

    def any(self):
        """
        Add an argument that matches anything.

        :return: builder
        """
        return self.arg(r".*")

    def any_except(self, char):
        """
        Adds an argument that matches anything other than a specified character (useful for commands containing
        delimiters)

        :param char: the character not to match
        :return: builder
        """
        return self.arg(r"[^{}]*".format(re.escape(char)))

    def build(self, *args, **kwargs):
        """
        Builds the CMd object based on the target and regular expression.

        :param args: arguments to pass to Cmd constructor
        :param kwargs: key word arguments to pass to Cmd constructor
        :return: Cmd object
        """
        if self._ignore_case:
            pattern = regex(self._reg_ex)
            pattern.compiled_pattern = re.compile(self._reg_ex.encode(), re.IGNORECASE)
        else:
            pattern = self._reg_ex
        return Cmd(
            self._target_method,
            pattern,
            argument_mappings=self.argument_mappings,
            *args,
            **kwargs
        )

    def add_ascii_character(self, char_number):
        """
        Add a single character based on its integer value, e.g. 49 is 'a'.

        :param char_number: character number
        :return: self
        """
        self._add_to_regex(chr(char_number), False)
        return self

    def stx(self):
        """
        Add the STX character (0x2) to the string.

        :return: builder
        """
        return self.escape(STX)

    def etx(self):
        """
        Add the ETX character (0x3) to the string.

        :return: builder
        """
        return self.escape(ETX)

    def eot(self):
        """
        Add the EOT character (0x4) to the string.

        :return: builder
        """
        return self.escape(EOT)

    def enq(self):
        """
        Add the ENQ character (0x5) to the string.

        :return: builder
        """
        return self.escape(ENQ)

    def ack(self):
        """
        Add the ACK character (0x6) to the string.

        :return: builder
        """
        return self.escape(ACK)

    def eos(self):
        """
        Adds the regex end-of-string character to a command.

        :return: builder
        """
        self._reg_ex += "$"
        return self

    def get_multicommands(self, command_separator):
        """
        Allows emulator to split multiple commands separated by a defined command separator, e.g. ";".
        Must be accompanied by stream device methods. See Keithley 2700 for examples

        :param command_separator: Character(s) that separate commands
        :return: builder
        """
        self.arg("[^" + re.escape(command_separator) + "]*").escape(
            command_separator
        ).arg(".*")
        return self
