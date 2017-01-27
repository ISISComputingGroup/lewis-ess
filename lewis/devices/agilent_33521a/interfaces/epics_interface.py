# -*- coding: utf-8 -*-
# *********************************************************************
# lewis - a library for creating hardware device simulators
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

from lewis.adapters.epics import EpicsAdapter, PV


class Agilent33521AEpicsInterface(EpicsAdapter):
    """
    A minimal EPICS interface to the Agilent 33521A function generator. It exposes
    three key features of the device: Frequency, amplitude and phase of the generated
    function.

    Should the connection to the function generator be lost for any reason, its possible
    to recover from that situation by writing a number greater than 0 to the Reset-PV.
    """
    pvs = {
        'ActFreq': PV('frequency', read_only=True),
        'Freq': PV('target_frequency', meta_data_property='frequency_meta'),

        'ActAmp': PV('amplitude', read_only=True),
        'Amp': PV('target_amplitude', meta_data_property='amplitude_meta'),

        'ActPhase': PV('phase', read_only=True),
        'Phase': PV('target_phase', meta_data_property='phase_meta'),

        'Err': PV('error_message', read_only=True, type='string'),
        'Reset': PV('reset', type='int')
    }

    @property
    def reset(self):
        """
        Writing any integer greater than 0 to this field tries to reset
        the error state of the device. Its value is always 0.
        """
        return 0

    @reset.setter
    def reset(self, do_reset):
        if do_reset > 0:
            self._device.reset()
