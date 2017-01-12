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
# References Used:
#   http://www.modbus.org/docs/Modbus_Application_Protocol_V1_1b3.pdf
#   http://www.modbus.org/docs/Modbus_Messaging_Implementation_Guide_V1_0b.pdf
#   https://github.com/sourceperl/pyModbusTCP
#   https://github.com/bashwork/pymodbus
# *********************************************************************


from __future__ import division

import socket
import asyncore
import struct
import inspect

from copy import deepcopy
from math import ceil
from collections import OrderedDict

from lewis.core.statemachine import StateMachine
from lewis.adapters import Adapter


class MBFC(object):
    """Modbus standard function codes"""
    READ_COILS = 0x01
    READ_DISCRETE_INPUTS = 0x02
    READ_HOLDING_REGISTERS = 0x03
    READ_INPUT_REGISTERS = 0x04
    WRITE_SINGLE_COIL = 0x05
    WRITE_SINGLE_REGISTER = 0x06
    WRITE_MULTIPLE_COILS = 0x0F
    WRITE_MULTIPLE_REGISTERS = 0x10
    # MODBUS_ENCAPSULATED_INTERFACE = 0x2B

    @classmethod
    def is_valid(cls, code):
        # Adapted from: http://stackoverflow.com/a/4241225/3827434
        boring = dir(type('dummy', (object,), {}))
        codes = dict([attr for attr in inspect.getmembers(cls) if attr[0] not in boring])
        return code in codes.values()


class MBEX(object):
    """Modbus standard exception codes"""
    NONE = 0x00
    ILLEGAL_FUNCTION = 0x01
    DATA_ADDRESS = 0x02
    DATA_VALUE = 0x03
    SLAVE_DEVICE_FAILURE = 0x04
    ACKNOWLEDGE = 0x05
    SLAVE_DEVICE_BUSY = 0x06
    MEMORY_PARITY_ERROR = 0x08
    GATEWAY_PATH_UNAVAILABLE = 0x0A
    GATEWAY_TARGET_DEVICE_FAILED_TO_RESPOND = 0x0B


class ModbusBasicDatabank(object):
    def __init__(self):
        self.bits = [False] * 0x10000
        self.words = [0] * 0x10000

    def get_bits(self, address, count=1):
        bits = self.bits[address:address+count]
        return bits if len(bits) == count else None

    def set_bits(self, address, values):
        end = address + len(values)
        if 0 <= address <= len(self.bits) - end:
            self.bits[address:end] = values

    def get_words(self, address, count=1):
        bits = self.bits[address:address + count]
        return bits if len(bits) == count else None

    def set_words(self, address, values):
        end = address + len(values)
        if 0 <= address <= len(self.words) - end:
            self.words[address:end] = values

    def validate_bits(self, address, count=1):
        return 0 <= address + count <= 0x10000

    def validate_words(self, address, count=1):
        return 0 <= address + count <= 0x10000


class ModbusTCPFrame(object):
    def __init__(self, stream=None):
        self.transaction_id = 0
        self.protocol_id = 0
        self.length = 2
        self.unit_id = 0
        self.fcode = 0
        self.data = bytearray()

        if stream is not None:
            self.from_bytearray(stream)

    def from_bytearray(self, stream):
        """
        Constructs this frame from input data stream, consuming as many bytes as necessary from
        the beginning of the stream.

        If stream does not contain enough data to construct a complete modbus frame, an EOFError
        is raised and no data is consumed.

        :param stream: bytearray to consume data from to construct this frame.
        :except EOFError Not enough data for complete frame; no data consumed.
        """
        fmt = '>HHHBB'
        size_header = struct.calcsize(fmt)
        if len(stream) < size_header:
            raise EOFError

        (
            self.transaction_id,
            self.protocol_id,
            self.length,
            self.unit_id,
            self.fcode
        ) = struct.unpack(fmt, bytes(stream[:size_header]))

        size_total = size_header + self.length - 2
        if len(stream) < size_total:
            raise EOFError

        self.data = stream[size_header:size_total]
        del stream[:size_total]

    def to_bytearray(self):
        """
        Convert this frame into its bytearray representation.

        :return: bytearray representation of this frame.
        """
        header = bytearray(struct.pack(
            '>HHHBB',
            self.transaction_id,
            self.protocol_id,
            self.length,
            self.unit_id,
            self.fcode
        ))
        return header + self.data

    def is_valid(self):
        """
        Check integrity and validity of this frame.

        :return: bool True if this frame is structurally valid.
        """
        conditions = [
            self.protocol_id == 0,  # Modbus always uses protocol 0
            2 <= self.length <= 260,  # Absolute length limits
            len(self.data) == self.length - 2,  # Total length matches data length
        ]
        return all(conditions)

    def create_exception(self, code):
        """
        Create an exception frame based on this frame.

        :param code: Modbus exception code to use for this exception
        :return: ModbusTCPFrame instance that represents an exception
        """
        frame = deepcopy(self)
        frame.length = 3
        frame.fcode += 0x80
        frame.data = bytearray(chr(code))
        return frame

    def create_response(self, data=None):
        """
        Create a response frame based on this frame.

        :param data: Data section of response as bytearray. If None, request data section is kept.
        :return: ModbusTCPFrame instance that represents a response
        """
        frame = deepcopy(self)
        if data is not None:
            frame.data = data
        frame.length = 2 + len(frame.data)
        return frame


class ModbusProtocol(object):
    """
    StateMachine based Modbus Protocol parser.
    """

    def _init_state(self):
        self._request = None
        self._response = None
        self._exception = None

    def __init__(self, handler, databank):
        self._init_state()

        self.handler = handler
        self.databank = databank
        self.buffer = bytearray()

        self.protocol = StateMachine({
            'initial': 'await_request',
            'transitions': OrderedDict([
                (('await_request', 'check_fcode'), lambda: self._request is not None),
                (('check_fcode', 'send_response'), lambda: self._exception is not None),

                (('check_fcode', 'read_bit'),
                 lambda: self._request.fcode in
                    (MBFC.READ_COILS, MBFC.READ_DISCRETE_INPUTS)),
                (('check_fcode', 'read_word'),
                 lambda: self._request.fcode in
                    (MBFC.READ_HOLDING_REGISTERS, MBFC.READ_INPUT_REGISTERS)),
                (('check_fcode', 'write_coil'),
                 lambda: self._request.fcode == MBFC.WRITE_SINGLE_COIL),
                (('check_fcode', 'write_register'),
                 lambda: self._request.fcode == MBFC.WRITE_SINGLE_REGISTER),

                (('read_bit', 'send_response'), lambda: True),
                (('read_word', 'send_response'), lambda: True),
                (('write_coil', 'send_response'), lambda: True),
                (('write_register', 'send_response'), lambda: True),
                (('send_response', 'await_request'), lambda: True),

                # Print unknown packets
                (('check_fcode', 'print_packet'), lambda: True),
                (('print_packet', 'await_request'), lambda: True),
            ])
        })
        self.protocol.bind_handlers_by_name(self, prefix=['_on_', '_in_', '_after_'])
        self.protocol.process()  # Cycle into initial state

    def parse(self, data=None):
        """
        Parse as much of current buffer as possible.

        :param data: Optionally append given data to buffer prior to parsing
        """
        self.buffer.extend(bytearray(data or ''))

        # Process until two or three FSM cycles stay in the same state
        prevstate = None
        while prevstate != self.protocol.state:
            prevstate = self.protocol.state
            self.protocol.process()
            self.protocol.process()

    def _on_await_request(self):
        """Re-initialize for a clean start to parsing"""
        self._init_state()

    def _in_await_request(self):
        """Try loading a Modbus request from buffer"""
        try:
            self._request = ModbusTCPFrame(self.buffer)
        except EOFError:
            # Buffer doesn't contain enough data
            # This is fine; we just keep waiting
            self._request = None

    def _on_check_fcode(self):
        """Validate Modbus Function Code"""
        if not MBFC.is_valid(self._request.fcode):
            self._exception = MBEX.ILLEGAL_FUNCTION

    def _on_print_packet(self):
        print("Unsupported!")
        # from pprint import pprint
        # pprint(vars(self._request))

    def _on_read_bit(self):
        """Process Coil or Discrete Input read request when data arrives"""
        addr, count = struct.unpack('>HH', bytes(self._request.data))

        if not 0x0001 <= count <= 0x07D0:
            self._exception = MBEX.DATA_VALUE
            return

        if not self.databank.validate_bits(addr, count):
            self._exception = MBEX.DATA_ADDRESS
            return

        # Get response data
        bits = self.databank.get_bits(addr, count)
        byte_count = int(ceil(len(bits) / 8))
        byte_list = bytearray(byte_count)

        # Bits to bytes: LSB -> MSB, first byte -> last byte
        for i, bit in enumerate(bits):
            byte_list[int(i / 8)] |= (bit << i % 8)

        # Construct response
        data = struct.pack('>B%dB' % byte_count, byte_count, *list(byte_list))
        self._response = self._request.create_response(data)

        print("Read BIT request for {} items at address {}.".format(count, addr))

    def _on_read_word(self):
        """Process Holding Register or Input Register read request when data arrives"""
        addr, count = struct.unpack('>HH', bytes(self._request.data))

        if not 0x0001 <= count <= 0x007D:
            self._exception = MBEX.DATA_VALUE
            return

        if not self.databank.validate_words(addr, count):
            self._exception = MBEX.DATA_ADDRESS
            return

        # Get response data
        words = self.databank.get_words(addr, count)
        byte_count = len(words) * 2

        # Construct response
        data = struct.pack('>B%dH' % len(words), byte_count, *list(words))
        self._response = self._request.create_response(data)

        print("Read WORD request for {} items at address {}.".format(count, addr))

    def _on_write_coil(self):
        """Process Write Single Coil request"""
        addr, value = struct.unpack('>HH', bytes(self._request.data))
        value = {0x0000: False, 0xFF00: True}.get(value, None)

        if value is None:
            self._exception = MBEX.DATA_VALUE
            return

        if not self.databank.validate_bits(addr):
            self._exception = MBEX.DATA_ADDRESS
            return

        self.databank.set_bits(addr, [value])
        self._response = self._request.create_response()

        print("Write BIT request for value {} at address{}".format(value, addr))

    def _on_write_register(self):
        """Process Write Single Register request"""
        addr, value = struct.unpack('>HH', bytes(self._request.data))

        if not self.databank.validate_words(addr):
            self._exception = MBEX.DATA_ADDRESS
            return

        self.databank.set_words(addr, [value])
        self._response = self._request.create_response()

        print("Write WORD request for value {} at address{}".format(value, addr))

    def _on_send_response(self):
        if self._exception is not None:
            print("Exception!")
            self._response = self._request.create_exception(self._exception)

        # print("Response!")
        # from pprint import pprint
        # pprint(vars(self._response))

        self.handler.send(self._response.to_bytearray())


class ModbusHandler(asyncore.dispatcher_with_send):
    def __init__(self, sock, target):
        asyncore.dispatcher_with_send.__init__(self, sock=sock)
        self.databank = target.databank
        self.parser = ModbusProtocol(self, self.databank)
        self.target = target

    def handle_read(self):
        data = self.recv(8192)
        hexdata = str([c.encode('hex') for c in data])
        print(">>> " + hexdata)
        self.parser.parse(data)

    def handle_close(self):
        print("Client from %s disconnected." % repr(self.addr))
        self.close()


class ModbusServer(asyncore.dispatcher):
    def __init__(self, host, port, target=None):
        asyncore.dispatcher.__init__(self)
        self.target = target
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            print("Client connect from %s" % repr(addr))
            ModbusHandler(sock, self.target)

    def handle_close(self):
        pass


class ModbusAdapter(Adapter):
    protocol = 'modbus'
    databank = None

    def __init__(self, device, arguments=None):
        super(ModbusAdapter, self).__init__(device, arguments)

        if arguments is not None:
            self._options = self._parse_arguments(arguments)

        self._server = None

        if self.databank is None:
            raise RuntimeError("Must specify a databank to use ModbusAdapter.")

    def _parse_arguments(self, arguments):
        return {}

    def start_server(self):
        self._server = ModbusServer('localhost', 5020, self)

    def stop_server(self):
        if self._server is not None:
            self._server.close()
            self._server = None

    @property
    def is_running(self):
        return self._server is not None

    def handle(self, cycle_delay=0.1):
        asyncore.loop(cycle_delay, count=1)
