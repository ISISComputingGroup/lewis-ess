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

from lewis.core.utils import check_limits
from lewis.devices.socket_device import SocketDevice
from lewis.adapters.epics import EpicsAdapter, PV


class DelftMagnet(SocketDevice):
    poll_map = {
        '_b1_target': ('REQ B1;', float),
        '_b2_target': ('REQ B2;', float),
        '_b3_target': ('REQ B3', float),
        '_b4_target': ('REQ B4', float),
        '_measured_values': ('REQ ALLF;', str),
    }

    in_terminator = '\r\n'
    out_terminator = '\r\n'

    def _initialize_data(self):
        self._amplitude = 0.0

        self._b1_target = 0.0
        self._b2_target = 0.0
        self._b3_target = 0.0
        self._b4_target = 0.0

        self._prec = 0.0
        self._upper_limit = 0.0

        self._measured_values = ''

    def on_connected(self):
        self._update_meta()

    def _update_meta(self):
        self.update('_prec', 'REQ EM;')
        self.update('_upper_limit', 'REQ LI;')

    @property
    def b1(self):
        """Value of magnetic field B1 in mT."""
        return float(self._measured_values.split(',')[0])

    @property
    def b1_target(self):
        """Target value of magnetic field B1 in mT."""
        return self._b1_target

    @b1_target.setter
    @check_limits(0.0, '_upper_limit')
    def b1_target(self, new_b1_target):
        self.write('SET B1%f' % new_b1_target)

    @property
    def b2(self):
        """Value of magnetic field B2 in mT."""
        return float(self._measured_values.split(',')[1])

    @property
    def b2_target(self):
        """Target value of magnetic field B2 in mT."""
        return self._b2_target

    @b2_target.setter
    @check_limits(0.0, '_upper_limit')
    def b2_target(self, new_b2_target):
        self.write('SET B2%f' % new_b2_target)

    @property
    def b3(self):
        """Value of magnetic field B3 in mT."""
        return float(self._measured_values.split(',')[2])

    @property
    def b3_target(self):
        """Target value of magnetic field B3 in mT."""
        return self._b3_target

    @b3_target.setter
    @check_limits(0.0, '_upper_limit')
    def b3_target(self, new_b3_target):
        self.write('SET B3%f' % new_b3_target)

    @property
    def b4(self):
        """Value of magnetic field B4 in mT."""
        return float(self._measured_values.split(',')[3])

    @property
    def b4_target(self):
        """Target value of magnetic field B4 in mT."""
        return self._b4_target

    @b4_target.setter
    @check_limits(0.0, '_upper_limit')
    def b4_target(self, new_b4_target):
        self.write('SET B4%f' % new_b4_target)

    @property
    def all_meta(self):
        return {
            'hilim': self._upper_limit,
            'lolim': 0.0,
            'prec': self._prec,
        }


class DelftMagnetEpicsInterface(EpicsAdapter):
    pvs = {
        'ActB1': PV('b1', read_only=True),
        'B1-RB': PV('b1_target', read_only=True),
        'B1': PV('b1_target', meta_data_property='all_meta'),

        'ActB2': PV('b2', read_only=True),
        'B2-RB': PV('b2_target', read_only=True),
        'B2': PV('b2_target', meta_data_property='all_meta'),

        'ActB3': PV('b3', read_only=True),
        'B3-RB': PV('b3_target', read_only=True),
        'B3': PV('b3_target', meta_data_property='all_meta'),

        'ActB4': PV('b4', read_only=True),
        'B4-RB': PV('b4_target', read_only=True),
        'B4': PV('b4_target', meta_data_property='all_meta'),
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


setups = dict(
    default=dict(
        device_type=DelftMagnet,
        parameters=dict(
            override_initial_data=dict(
                connection_string='192.168.1.1:4001',
                retry_wait=10.0, max_retries=5, poll_interval=5.0, timeout=0.25
            ),
        )
    )
)
