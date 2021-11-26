#!/usr/bin/env python
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

from setuptools import find_packages, setup


# as suggested on http://python-packaging.readthedocs.io/en/latest/metadata.html
def readme():
    with open("README.rst") as f:
        return f.read()


setup(
    name="lewis",
    version="1.3.1",
    description="Lewis - Let's write intricate simulators!",
    long_description=readme(),
    url="https://github.com/ess-dmsc/lewis",
    author="ScreamingUdder",
    license="GPL v3",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
    ],
    keywords="hardware simulation controls",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.6.0",
    install_requires=["pyzmq", "json-rpc", "semantic_version", "PyYAML", "scanf"],
    extras_require={
        "epics": ["pcaspy"],
        "dev": [
            "flake8",
            "mock",
            "sphinx",
            "sphinx_rtd_theme",
            "pytest",
            "pytest-cov",
            "coverage",
            "tox",
            "approvaltests",
            "pytest-approvaltests",
        ],
    },
    entry_points={
        "console_scripts": [
            "lewis=lewis.scripts.run:run_simulation",
            "lewis-control=lewis.scripts.control:control_simulation",
        ],
    },
)
