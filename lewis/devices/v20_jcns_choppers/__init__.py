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
from lewis.core.logging import has_log
from lewis.devices.socket_device import SocketDevice
from lewis.adapters.epics import EpicsAdapter, PV
from lewis.adapters import ForwardProperty
from collections import OrderedDict


def ok_nok(str_val):
    return 0 if str_val.upper() == 'OK' else 1


class zero_if_match(object):
    def __init__(self, matches):
        self.matches = matches

    def __call__(self, str_val):
        return 0 if str_val.upper() == self.matches else 1


class JCNSChopperCascade(SocketDevice):
    poll_map = {
        '_asta': ('C01?;ASTA?', str),
    }

    state = {
        'C01': {},
        'C02': {},
        'C03': {},
        'C04': {}
    }

    fields = [('RSPE', float), ('SSPE', float), ('FACT', int), ('SPEE', float), ('SPHA', float),
              ('PHAS', float), ('PHOK', ok_nok), ('MBON', str), ('MBOK', ok_nok),
              ('MBIN', float), ('DRON', zero_if_match('ON')), ('SDRI', zero_if_match('START')),
              ('DRL1', float), ('DRL2', float),
              ('DRL3', float), ('RODI', zero_if_match('CLOCK')), ('PPOS', ok_nok), ('DRIT', float),
              ('INCL', float),
              ('SYCL', float), ('OUPH', float), ('MACH', str), ('LOON', str),
              ('LMSR', zero_if_match('OK')),
              ('DSPM', ok_nok), ('EROK', ok_nok), ('VAOK', ok_nok), ('SMOK', ok_nok),
              ('MBAT', ok_nok), ('MBAC', ok_nok), ('DRAT', ok_nok), ('DRAC', ok_nok),
              ('PSOK', ok_nok)]

    in_terminator = '\r\n'
    out_terminator = '\r\n'

    def _initialize_data(self):
        pass

    @property
    def _asta(self):
        return ''

    @_asta.setter
    def _asta(self, new_asta):
        elements = new_asta.strip().split(';')[2:]

        for i, name in enumerate(self.state.keys()):
            start_idx = i * (len(self.fields) + 1) + 1
            end_idx = start_idx + len(self.fields)
            self.state[name] = {field[0]: field[1](val) for field, val in
                                zip(self.fields, elements[start_idx:end_idx])}


class JCNSChopperEpicsInterface(object):
    pvs = OrderedDict([
        ('Factor', PV('factor', type='int')),
        ('Drive', PV('drive', type='enum', enums=['START', 'STOP'])),
        ('DrivePower', PV('drive_power', type='enum', enums=['ON', 'OFF'], read_only=True)),
        ('DriveTemp', PV('drive_temperature', read_only=True)),
        ('Phase', PV('phase', read_only=True)),
        ('Phase-SP', PV('phase_setpoint')),
        ('Direction', PV('direction', type='enum', enums=['CLOCK', 'ANTICLOCK'], read_only=True)),
        ('Speed', PV('speed', read_only=True)),
        ('Speed-SP', PV('speed_setpoint', read_only=True)),
        ('Status', PV('status', type='int', read_only=True)),
        ('MotionStage',
         PV('motion_stage_status', type='enum', enums=['RELEASED', 'LOCKED'], read_only=True))
    ])

    def _get_device_state(self, key):
        return self._device.state[self.pv_prefix].get(key)

    def _set_device_state(self, key, value):
        self._device.state[self.pv_prefix][key] = value

    pv_prefix = None

    def __init__(self, device):
        self._device = device

    @property
    def factor(self):
        return self._get_device_state('FACT')

    @factor.setter
    @check_limits(1, 5)
    def factor(self, new_factor):
        self._device.write('%s!;FACT!;%d' % (self.pv_prefix, new_factor))
        self._set_device_state('FACT', new_factor)

    @property
    def drive(self):
        return self._get_device_state('SDRI')

    @drive.setter
    def drive(self, new_state):
        new_state_cmd = 'START' if new_state == 0 else 'STOP'
        self._device.write(
            '%s!;DRIV!;%s' % (self.pv_prefix, new_state_cmd))
        self._set_device_state('SDRI', new_state_cmd)

    @property
    def drive_power(self):
        return self._get_device_state('DRON')

    @property
    def phase(self):
        return self._get_device_state('PHAS')

    @property
    def phase_setpoint(self):
        return self._get_device_state('SPHA')

    @phase_setpoint.setter
    @check_limits(0, 360)
    def phase_setpoint(self, new_setpoint):
        self._device.write('%s!;PHAS!;%.2f' % (self.pv_prefix, new_setpoint))
        self._set_device_state('SPHA', new_setpoint)

    @property
    def drive_temperature(self):
        return self._get_device_state('DRIT')

    @property
    def direction(self):
        return self._get_device_state('RODI')

    @property
    def speed(self):
        return self._get_device_state('SPEE')

    @property
    def speed_setpoint(self):
        return self._get_device_state('SSPE')

    @property
    def status(self):
        ret = 0
        for field in self._device.fields:
            if field[1] == ok_nok:
                ret = (ret << 1) | (self._get_device_state(field[0]) or 0)

        return ret

    @property
    def motion_stage_status(self):
        return self._get_device_state('LMSR')


class JCNSChopperCascadeEpicsInterface(EpicsAdapter):
    pvs = OrderedDict()

    def __init__(self, device, arguments=None):
        for name in ('C01', 'C02', 'C03', 'C04'):
            chopper = JCNSChopperEpicsInterface(device)
            chopper.pv_prefix = name

            setattr(self, name, chopper)

            pref = chopper.pv_prefix
            for pv_name, pv in chopper.pvs.items():
                new_prop = pref + '_' + pv.property
                real_pv = pref + ':' + pv_name
                self.pvs[real_pv] = PV(new_prop, pv.poll_interval,
                                       pv.read_only, pv.meta_data_property, pv.doc,
                                       **pv.config)

                setattr(type(self), new_prop, ForwardProperty(name, pv.property, instance=self))

        super(JCNSChopperCascadeEpicsInterface, self).__init__(device, arguments)


setups = dict(
    default=dict(
        device_type=JCNSChopperCascade,
        parameters=dict(
            override_initial_data=dict(
                connection_string='',
                retry_wait=10.0, max_retries=5, poll_interval=2.0, timeout=0.5,
            ),
        )
    )
)
