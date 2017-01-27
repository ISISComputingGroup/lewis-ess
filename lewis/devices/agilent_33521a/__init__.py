# -*- coding: utf-8 -*-
# *********************************************************************
# lewis - a library for creating hardware device simulators
# Copyright (C) 2016-2017 European Spallation Source ERIC
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

from lewis.core.utils import check_limits
from lewis.devices.socket_device import SocketDevice


class Agilent33521A(SocketDevice):
    poll_map = {
        '_amplitude': ('VOLTAGE?', float),
        '_frequency': ('FREQUENCY?', float),
        '_phase': ('PHASE?', float),
    }

    in_terminator = '\n'
    out_terminator = '\n'

    def _initialize_data(self):
        self._amplitude = 0.0
        self._target_amplitude = 0.0
        self._target_amplitude_min = 0.0
        self._target_amplitude_max = 0.0

        self._frequency = 0.0
        self._target_frequency = 0.0
        self._target_frequency_min = 0.0
        self._target_frequency_max = 0.0

        self._phase = 0.0
        self._target_phase = 0.0
        self._target_phase_min = 0.0
        self._target_phase_max = 0.0

    def on_connected(self):
        self._update_limits()

    def _update_limits(self):
        self.update('_target_amplitude_min', 'VOLTAGE? MIN')
        self.update('_target_amplitude_max', 'VOLTAGE? MAX')
        self.update('_target_frequency_min', 'FREQUENCY? MIN')
        self.update('_target_frequency_max', 'FREQUENCY? MAX')
        self.update('_target_phase_min', 'PHASE? MIN')
        self.update('_target_phase_max', 'PHASE? MAX')

    @property
    def amplitude(self):
        """Amplitude of the signal in Volts"""
        return self._amplitude

    @property
    def target_amplitude(self):
        """Target amplitude of the signal in Volts"""
        return self._target_amplitude

    @target_amplitude.setter
    @check_limits('_target_amplitude_min', '_target_amplitude_max')
    def target_amplitude(self, new_target_amplitude):
        self._target_amplitude = new_target_amplitude
        self.write('VOLTAGE %f' % new_target_amplitude)

    @property
    def amplitude_meta(self):
        return {
            'hilim': self._target_amplitude_max,
            'lolim': self._target_amplitude_min,
        }

    @property
    def frequency(self):
        """Frequency of the signal in Hz."""
        return self._frequency

    @property
    def target_frequency(self):
        """Target frequency of the signal in Hz."""
        return self._target_frequency

    @target_frequency.setter
    @check_limits('_target_frequency_min', '_target_frequency_max')
    def target_frequency(self, new_frequency):
        self._target_frequency = new_frequency
        self.write('FREQUENCY %f' % new_frequency)

    @property
    def frequency_meta(self):
        return {
            'hilim': self._target_frequency_max,
            'lolim': self._target_frequency_min,
        }

    @property
    def phase(self):
        """Phase of the signal in degrees."""
        return self._phase

    @property
    def target_phase(self):
        """Target phase of the signal in degrees."""
        return self._target_phase

    @target_phase.setter
    @check_limits('_target_phase_min', '_target_phase_max')
    def target_phase(self, new_phase):
        self._target_phase = new_phase
        self.write('PHASE %f' % new_phase)

    @property
    def phase_meta(self):
        return {
            'hilim': self._target_phase_max,
            'lolim': self._target_phase_min,
        }


setups = dict(
    default=dict(
        device_type=Agilent33521A,
        parameters=dict(
            override_initial_data=dict(
                connection_string='192.168.1.104:5025',
                retry_wait=10.0, max_retries=5, poll_interval=5.0, timeout=0.5,
            ),
        )
    )
)
