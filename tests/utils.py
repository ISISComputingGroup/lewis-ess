# -*- coding: utf-8 -*-
# *********************************************************************
# lewis - a library for creating hardware device simulators
# Copyright (C) 2016-2020 European Spallation Source ERIC
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

import os
import shutil
import sys
import tempfile
import unittest


def assertRaisesNothing(testobj, func, *args, **kwargs):
    """
    unittest does not have an assertRaisesNothing. This function adopted from
    the Mantid testhelpers module provides that functionality.

    :param testobj: A unittest object
    :param func: A callable object
    :param *args: Positional arguments passed to the callable as they are
    :param **kwargs: Keyword arguments, passed on as they are
    """
    try:
        return func(*args, **kwargs)
    except Exception as exc:
        testobj.fail(
            "Assertion error. An exception was caught where none "
            "was expected in %s. Message: %s" % (func.__name__, str(exc))
        )


class TestWithPackageStructure(unittest.TestCase):
    """
    This is an intermediate class that creates a package structure in the
    system's temporary file directory. The structure is as follows:

        tmp_dir (random name)
         |
         +- some_dir
         |   |
         |   +- __init__.py
         +- .invalid
         +- _invalid
         +- some_file.py
         +- some_other_file.pyc
         +- _some_invalid_file.py
         +- __init__.py

    All files are empty and the entire structure is deleted in the tearDown.
    """

    @classmethod
    def setUpClass(cls):
        cls._tmp_dir = tempfile.mkdtemp()
        cls._tmp_package = tempfile.mkdtemp(dir=cls._tmp_dir)
        cls._tmp_package_name = os.path.basename(cls._tmp_package)

        cls._files = {
            k: os.path.join(cls._tmp_package, v)
            for k, v in dict(
                valid="some_file.py",
                invalid_ext="some_other_file.pyc",
                invalid_name="_some_invalid_file.py",
                failing_module="failing_module.py",
            ).items()
        }

        for abs_file_name in cls._files.values():
            with open(abs_file_name, mode="w"):
                pass

        with open(cls._files["failing_module"], mode="w") as fh:
            fh.write("raise ImportError()\n")

        cls._dirs = {
            k: os.path.join(cls._tmp_package, v)
            for k, v in dict(
                valid="some_dir", invalid_underscore="_invalid", invalid_dot=".invalid"
            ).items()
        }

        for abs_dir_name in cls._dirs.values():
            os.mkdir(abs_dir_name)

        with open(os.path.join(cls._tmp_package, "__init__.py"), "w"):
            pass

        with open(os.path.join(cls._tmp_package, "some_dir", "__init__.py"), "w"):
            pass

        cls._expected_modules = ["some_dir", "some_file"]

        sys.path.insert(0, cls._tmp_dir)

    @classmethod
    def tearDownClass(cls):
        sys.path.pop(sys.path.index(cls._tmp_dir))
        shutil.rmtree(cls._tmp_dir)
