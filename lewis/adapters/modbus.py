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

from copy import deepcopy
from math import ceil

from lewis.adapters import Adapter


class MBEX(object):
    """Modbus standard exception codes"""
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
    def __init__(self, sender, databank):
        """
        :param sender: callable that accepts one bytearray parameter, called to send responses.
        :param databank: ModbusDatabank instance to reference when processing requests
        """
        self._buffer = bytearray()
        self._databank = databank
        self._send = lambda req: sender(req.to_bytearray())

        self._fcode_handler_map = {
            0x01: self._handle_read_coils,
            0x02: self._handle_read_discrete_inputs,
            0x03: self._handle_read_holding_registers,
            0x04: self._handle_read_input_registers,
            0x05: self._handle_write_single_coil,
            0x06: self._handle_write_single_register,
            0x0F: self._handle_write_multiple_coils,
            0x10: self._handle_write_multiple_registers,
        }

    def process(self, data=None):
        """
        Process as much of current buffer as possible.

        :param data: Optionally append given data to buffer prior to parsing
        """
        self._buffer.extend(bytearray(data or ''))

        for request in self._buffered_requests():
            handler = self._get_handler(request.fcode)
            response = handler(request)
            self._send(response)

    def _buffered_requests(self):
        """Generator to yield all complete modbus requests in the buffer"""
        try:
            while True:
                yield ModbusTCPFrame(self._buffer)
        except EOFError:
            pass

    def _get_handler(self, fcode):
        """Return handler with signature handler(request) for function code fcode"""
        return self._fcode_handler_map.get(
            fcode,
            self._illegal_function_exception
        )

    def _illegal_function_exception(self, request):
        """Log and return an illegal function code exception"""
        print("Unsupported Function Code: {0} ({0:#04x})".format(request.fcode))
        return request.create_exception(MBEX.ILLEGAL_FUNCTION)

    def _handle_read_coils(self, request):
        """
        Handle request as per Modbus Application Protocol v1.1b3:
        Section 6.1 - (0x01) Read Coils

        :param request: ModbusTCPFrame containing the request
        :return: ModbusTCPFrame response to the request
        """
        addr, count = struct.unpack('>HH', bytes(request.data))

        if not 0x0001 <= count <= 0x07D0:
            return request.create_exception(MBEX.DATA_VALUE)

        if not self._databank.validate_bits(addr, count):
            return request.create_exception(MBEX.DATA_ADDRESS)

        # Get response data
        bits = self._databank.get_bits(addr, count)
        byte_count = int(ceil(len(bits) / 8))
        byte_list = bytearray(byte_count)

        # Bits to bytes: LSB -> MSB, first byte -> last byte
        for i, bit in enumerate(bits):
            byte_list[i // 8] |= (bit << i % 8)

        # Construct response
        print("Read COIL request for {} items at address {}.".format(count, addr))
        data = struct.pack('>B%dB' % byte_count, byte_count, *list(byte_list))
        return request.create_response(data)

    def _handle_read_discrete_inputs(self, request):
        """Handle a READ_DISCRETE_INPUTS request"""
        # TODO: Should not be the same; change once databank upgraded
        return self._handle_read_coils(request)

    def _handle_read_holding_registers(self, request):
        """Handle READ_HOLDING_REGISTERS request"""
        addr, count = struct.unpack('>HH', bytes(request.data))

        if not 0x0001 <= count <= 0x007D:
            return request.create_exception(MBEX.DATA_VALUE)

        if not self._databank.validate_words(addr, count):
            return request.create_exception(MBEX.DATA_ADDRESS)

        # Get response data
        words = self._databank.get_words(addr, count)
        byte_count = len(words) * 2

        # Construct response
        print("Read REGISTER request for {} items at address {}.".format(count, addr))
        data = struct.pack('>B%dH' % len(words), byte_count, *list(words))
        return request.create_response(data)

    def _handle_read_input_registers(self, request):
        """Handle READ_INPUT_REGISTERS request"""
        # TODO: Should not be the same; change once databank upgraded
        return self._handle_read_holding_registers(request)

    def _handle_write_single_coil(self, request):
        """Handle WRITE_SINGLE_COIL request"""
        addr, value = struct.unpack('>HH', bytes(request.data))
        value = {0x0000: False, 0xFF00: True}.get(value, None)

        if value is None:
            return request.create_exception(MBEX.DATA_VALUE)

        if not self._databank.validate_bits(addr):
            return request.create_exception(MBEX.DATA_ADDRESS)

        # Execute and respond
        print("Write COIL request for value {} at address{}".format(value, addr))
        self._databank.set_bits(addr, [value])
        return request.create_response()

    def _handle_write_single_register(self, request):
        """Handle WRITE_SINGLE_REGISTER request"""
        addr, value = struct.unpack('>HH', bytes(request.data))

        if not self._databank.validate_words(addr):
            return request.create_exception(MBEX.DATA_ADDRESS)

        # Execute and respond
        print("Write WORD request for value {} at address {}".format(value, addr))
        self._databank.set_words(addr, [value])
        return request.create_response()

    def _handle_write_multiple_coils(self, request):
        """Handle WRITE_MULTIPLE_COILS request"""
        addr, bit_count, byte_count = struct.unpack('>HHB', bytes(request.data[:5]))
        data = request.data[5:]

        if not 0x0001 <= bit_count <= 0x07B0 or byte_count != ceil(bit_count / 8):
            return request.create_exception(MBEX.DATA_VALUE)

        if not self._databank.validate_bits(addr, bit_count):
            return request.create_exception(MBEX.DATA_ADDRESS)

        # Bytes to bits: first byte -> last byte, LSB -> MSB
        bits = [False] * bit_count
        for i in range(bit_count):
            bits[i] = bool(data[i // 8] & (1 << i % 8))

        # Execute and respond
        print("Write Multi Coils request for values {} at address {}".format(bits, addr))
        self._databank.set_bits(addr, bits)
        return request.create_response(request.data[:4])

    def _handle_write_multiple_registers(self, request):
        """Handle WRITE_MULTIPLE_REGISTERS request"""
        addr, reg_count, byte_count = struct.unpack('>HHB', bytes(request.data[:5]))
        data = request.data[5:]

        if not 0x0001 <= reg_count <= 0x007B or byte_count != reg_count * 2:
            return request.create_exception(MBEX.DATA_VALUE)

        if not self._databank.validate_words(addr, reg_count):
            return request.create_exception(MBEX.DATA_ADDRESS)

        words = list(struct.unpack('>%dH' % reg_count, data))

        # Execute and respond
        print("Write Multi Registers request for values {} at address {}".format(words, addr))
        self._databank.set_words(addr, words)
        return request.create_response(request.data[:4])


class ModbusHandler(asyncore.dispatcher_with_send):
    def __init__(self, sock, target):
        asyncore.dispatcher_with_send.__init__(self, sock=sock)
        self.databank = target.databank
        self.modbus = ModbusProtocol(self.send, self.databank)
        self.target = target

    def handle_read(self):
        data = self.recv(8192)
        hexdata = str([c.encode('hex') for c in data])
        print(">>> " + hexdata)
        self.modbus.process(data)

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
