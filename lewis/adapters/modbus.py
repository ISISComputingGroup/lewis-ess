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
This module provides components to expose a Device via a Modbus-interface. The following resources
were used as guidelines and references for implementing the protocol:

 - http://www.modbus.org/docs/Modbus_Application_Protocol_V1_1b3.pdf
 - http://www.modbus.org/docs/Modbus_Messaging_Implementation_Guide_V1_0b.pdf
 - https://github.com/sourceperl/pyModbusTCP
 - https://github.com/bashwork/pymodbus

.. note::

    For an example how Modbus can be used in the current implementation, please look
    at lewis/examples/modbus_device.
"""

import asyncore
import socket
import struct
from copy import deepcopy
from math import ceil

from lewis.core.adapters import Adapter
from lewis.core.devices import InterfaceBase
from lewis.core.logging import has_log


class ModbusDataBank:
    """
    Preliminary DataBank implementation for Modbus.

    This is a very generic implementation of a databank for Modbus. It's meant to set the
    groundwork for future implementations. Only derived classes should be instantiated, not
    this class directly. The signature of this __init__ method is subject to change.

    :param kwargs: Configuration
    """

    def __init__(self, **kwargs):
        self._data = kwargs["data"]
        self._start_addr = kwargs["start_addr"]

    def get(self, addr, count):
        """
        Read list of ``count`` values at ``addr`` memory location in DataBank.

        :param addr: Address to read from
        :param count: Number of entries to retrieve
        :return: list of entry values
        :except IndexError: Raised if address range falls outside valid range
        """
        addr -= self._start_addr
        data = self._data[addr : addr + count]
        if len(data) != count:
            addr += self._start_addr
            raise IndexError(
                "Invalid address range [{:#06x} - {:#06x}]".format(addr, addr + count)
            )
        return data

    def set(self, addr, values):
        """
        Write list ``values`` to ``addr`` memory location in DataBank.

        :param addr: Address to write to
        :param values: list of values to write
        :except IndexError: Raised if address range falls outside valid range
        """
        addr -= self._start_addr
        end = addr + len(values)
        if not 0 <= addr <= end <= len(self._data):
            addr += self._start_addr
            raise IndexError(
                "Invalid address range [{:#06x} - {:#06x}]".format(
                    addr, addr + len(values)
                )
            )
        self._data[addr:end] = values


class ModbusBasicDataBank(ModbusDataBank):
    """
    A basic ModbusDataBank instance.

    This type of DataBank simply serves as a memory space for Modbus requests to read from and
    write to. It does not support binding addresses to attributes or functions of the device
    or interface. Example usage:

    .. sourcecode:: Python

        di = ModbusBasicDataBank(False, 0x1000, 0x1FFF)

    :param default_value: Value to initialize memory with
    :param start_addr: First valid address
    :param last_addr: Last valid address
    """

    def __init__(self, default_value=0, start_addr=0x0000, last_addr=0xFFFF):
        super(ModbusBasicDataBank, self).__init__(
            start_addr=start_addr, data=[default_value] * (last_addr - start_addr + 1)
        )


class ModbusDataStore:
    """Convenience struct to hold the four types of DataBanks in Modbus"""

    def __init__(self, di=None, co=None, ir=None, hr=None):
        self.di = di
        self.co = co
        self.ir = ir
        self.hr = hr


class MBEX:
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


class ModbusTCPFrame:
    """
    This class models a frame of the Modbus TCP protocol.

    It may be a request, a response or an exception. Typically, requests are constructed using the
    init method, while responses and exceptions are constructed by called create_request or
    create_exception on an instance that is a request.

    Note that data from the passed in bytearray stream is consumed. That is, bytes will be removed
    from the front of the bytearray if construction is successful.

    :param stream: bytearray to consume data from to construct this frame.
    :except EOFError: Not enough data for complete frame; no data consumed.
    """

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
        :except EOFError: Not enough data for complete frame; no data consumed.
        """
        fmt = ">HHHBB"
        size_header = struct.calcsize(fmt)
        if len(stream) < size_header:
            raise EOFError

        (
            self.transaction_id,
            self.protocol_id,
            self.length,
            self.unit_id,
            self.fcode,
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
        header = bytearray(
            struct.pack(
                ">HHHBB",
                self.transaction_id,
                self.protocol_id,
                self.length,
                self.unit_id,
                self.fcode,
            )
        )
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


@has_log
class ModbusProtocol:
    """
    This class implements the Modbus TCP Protocol.

    The user of this class should provide a ModbusDataStore instance that will be used to
    fulfill read and write requests, and a callable `sender` which accepts one bytearray
    parameter. The `sender` will be called whenever a response frame is generated, with a
    bytearray containing the response frame as the parameter.

    Processing occurs when the user calls ModbusProtocol.process(), passing in the raw frame
    data to process as a bytearray. The data may include multiple frames and partial frame
    fragments. Any data that could not be processed (due to incomplete frames) is buffered for
    the next call to process.

    :param sender: callable that accepts one bytearray parameter, called to send responses.
    :param datastore: ModbusDataStore instance to reference when processing requests
    """

    def __init__(self, sender, datastore):
        self._buffer = bytearray()
        self._datastore = datastore
        self._send = lambda req: sender(req.to_bytearray())

        # Lookup table to handle requests as per Modbus Application Protocol v1.1b3, Section 6.
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

    def process(self, data, device_lock):
        """
        Process as much of given data as possible.

        Any remainder, in case there is an incomplete frame at the end, is stored so that
        processing may continue where it left off when more data is provided.

        :param data: Incoming byte data. Must be compatible with bytearray.
        :param device_lock: threading.Lock instance that is acquired for device interaction.
        """
        self._buffer.extend(bytearray(data))

        with device_lock:
            for request in self._buffered_requests():
                self.log.debug(
                    "Request: %s",
                    str(["{:#04x}".format(c) for c in request.to_bytearray()]),
                )

                handler = self._get_handler(request.fcode)
                response = handler(request)

                self.log.debug(
                    "Response: %s",
                    str(["{:#04x}".format(c) for c in response.to_bytearray()]),
                )

                self._send(response)

    def _buffered_requests(self):
        """Generator to yield all complete modbus requests in the internal buffer"""
        try:
            while True:
                # ModbusTCPFrame constructor consumes bytes from front of buffer
                yield ModbusTCPFrame(self._buffer)
        except EOFError:
            pass

    def _get_handler(self, fcode):
        """
        Get an appropriate handler function for given Function Code.

        Will always return a valid handler function. But, if the Function Code is invalid or not
        supported, the handler function will merely return an ILLEGAL_FUNCTION exception frame.

        :param fcode: int Function Code which needs to be handled
        :return: callable which takes one request frame parameter and returns a response frame
        """
        return self._fcode_handler_map.get(fcode, self._illegal_function_exception)

    def _illegal_function_exception(self, request):
        """Log and return an illegal function code exception"""
        self.log.error(
            "Unsupported Function Code: {0} ({0:#04x})".format(request.fcode)
        )
        return request.create_exception(MBEX.ILLEGAL_FUNCTION)

    def _handle_read_coils(self, request):
        """
        Handle request as per Modbus Application Protocol v1.1b3:
        Section 6.1 - (0x01) Read Coils

        :param request: ModbusTCPFrame containing the request
        :return: ModbusTCPFrame response to the request
        """
        return self._do_read_bits(self._datastore.co, request)

    def _handle_read_discrete_inputs(self, request):
        """
        Handle request as per Modbus Application Protocol v1.1b3:
        Section 6.2 - (0x02) Read Discrete Inputs

        :param request: ModbusTCPFrame containing the request
        :return: ModbusTCPFrame response to the request
        """
        return self._do_read_bits(self._datastore.di, request)

    def _do_read_bits(self, databank, request):
        """
        Shared handler for FC 0x01 and FC 0x02.

        :param databank: DataBank to execute against (di or co)
        :param request: ModbusTCPFrame containing the request
        :return: ModbusTCPFrame response to the request
        """
        addr, count = struct.unpack(">HH", bytes(request.data))

        if not 0x0001 <= count <= 0x07D0:
            return request.create_exception(MBEX.DATA_VALUE)

        try:
            bits = databank.get(addr, count)
            bits = [bool(bit) for bit in bits]
        except IndexError:
            return request.create_exception(MBEX.DATA_ADDRESS)

        # Bits to bytes: LSB -> MSB, first byte -> last byte
        byte_count = int(ceil(len(bits) / 8))
        byte_list = bytearray(byte_count)
        for i, bit in enumerate(bits):
            byte_list[i // 8] |= bit << i % 8

        # Construct response
        data = struct.pack(">B%dB" % byte_count, byte_count, *list(byte_list))
        return request.create_response(data)

    def _handle_read_holding_registers(self, request):
        """
        Handle request as per Modbus Application Protocol v1.1b3:
        Section 6.3 - (0x03) Read Holding Registers

        :param request: ModbusTCPFrame containing the request
        :return: ModbusTCPFrame response to the request
        """
        return self._do_read_registers(self._datastore.hr, request)

    def _handle_read_input_registers(self, request):
        """
        Handle request as per Modbus Application Protocol v1.1b3:
        Section 6.4 - (0x04) Read Input Registers

        :param request: ModbusTCPFrame containing the request
        :return: ModbusTCPFrame response to the request
        """
        return self._do_read_registers(self._datastore.ir, request)

    def _do_read_registers(self, databank, request):
        """
        Shared handler for FC 0x03 and FC 0x04.

        :param databank: DataBank to execute against (ir or hr)
        :param request: ModbusTCPFrame containing the request
        :return: ModbusTCPFrame response to the request
        """
        addr, count = struct.unpack(">HH", bytes(request.data))

        if not 0x0001 <= count <= 0x007D:
            return request.create_exception(MBEX.DATA_VALUE)

        try:
            words = databank.get(addr, count)
            words = [word & 0xFFFF for word in words]
        except IndexError:
            return request.create_exception(MBEX.DATA_ADDRESS)

        # Construct response
        data = struct.pack(">B%dH" % len(words), len(words) * 2, *words)
        return request.create_response(data)

    def _handle_write_single_coil(self, request):
        """
        Handle request as per Modbus Application Protocol v1.1b3:
        Section 6.5 - (0x05) Write Single Coil

        :param request: ModbusTCPFrame containing the request
        :return: ModbusTCPFrame response to the request
        """
        addr, value = struct.unpack(">HH", bytes(request.data))
        value = {0x0000: False, 0xFF00: True}.get(value, None)

        if value is None:
            return request.create_exception(MBEX.DATA_VALUE)

        try:
            self._datastore.co.set(addr, [value])
        except IndexError:
            return request.create_exception(MBEX.DATA_ADDRESS)

        # Respond to confirm
        return request.create_response()

    def _handle_write_single_register(self, request):
        """
        Handle request as per Modbus Application Protocol v1.1b3:
        Section 6.6 - (0x06) Write Single Register

        :param request: ModbusTCPFrame containing the request
        :return: ModbusTCPFrame response to the request
        """
        addr, value = struct.unpack(">HH", bytes(request.data))

        try:
            self._datastore.hr.set(addr, [value])
        except IndexError:
            return request.create_exception(MBEX.DATA_ADDRESS)

        # Respond to confirm
        return request.create_response()

    def _handle_write_multiple_coils(self, request):
        """
        Handle request as per Modbus Application Protocol v1.1b3:
        Section 6.11 - (0x0F) Write Multiple Coils

        :param request: ModbusTCPFrame containing the request
        :return: ModbusTCPFrame response to the request
        """
        addr, bit_count, byte_count = struct.unpack(">HHB", bytes(request.data[:5]))
        data = request.data[5:]

        if not 0x0001 <= bit_count <= 0x07B0 or byte_count != ceil(bit_count / 8):
            return request.create_exception(MBEX.DATA_VALUE)

        # Bytes to bits: first byte -> last byte, LSB -> MSB
        bits = [False] * bit_count
        for i in range(bit_count):
            bits[i] = bool(data[i // 8] & (1 << i % 8))

        try:
            self._datastore.co.set(addr, bits)
        except IndexError:
            return request.create_exception(MBEX.DATA_ADDRESS)

        # Respond to confirm
        return request.create_response(request.data[:4])

    def _handle_write_multiple_registers(self, request):
        """
        Handle request as per Modbus Application Protocol v1.1b3:
        Section 6.12 - (0x10) Write Multiple registers

        :param request: ModbusTCPFrame containing the request
        :return: ModbusTCPFrame response to the request
        """
        addr, reg_count, byte_count = struct.unpack(">HHB", bytes(request.data[:5]))
        data = request.data[5:]

        if not 0x0001 <= reg_count <= 0x007B or byte_count != reg_count * 2:
            return request.create_exception(MBEX.DATA_VALUE)

        try:
            words = list(struct.unpack(">%dH" % reg_count, data))
            self._datastore.hr.set(addr, words)
        except IndexError:
            return request.create_exception(MBEX.DATA_ADDRESS)

        # Respond to confirm
        return request.create_response(request.data[:4])


@has_log
class ModbusHandler(asyncore.dispatcher_with_send):
    def __init__(self, sock, interface, server):
        asyncore.dispatcher_with_send.__init__(self, sock=sock)
        self._datastore = ModbusDataStore(
            interface.di, interface.co, interface.ir, interface.hr
        )
        self._modbus = ModbusProtocol(self.send, self._datastore)
        self._server = server

        self._set_logging_context(interface)
        self.log.info("Client connected from %s:%s", *sock.getpeername())

    def handle_read(self):
        data = self.recv(8192)
        self._modbus.process(data, self._server.device_lock)

    def handle_close(self):
        self.log.info("Closing connection to client %s:%s", *self.socket.getpeername())
        self._server.remove_handler(self)
        self.close()


@has_log
class ModbusServer(asyncore.dispatcher):
    def __init__(self, host, port, interface, device_lock):
        asyncore.dispatcher.__init__(self)
        self.device_lock = device_lock
        self.interface = interface
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

        self._set_logging_context(interface)
        self.log.info("Listening on %s:%s", host, port)

        self._accepted_connections = []

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, _ = pair
            handler = ModbusHandler(sock, self.interface, self)
            self._accepted_connections.append(handler)

    def remove_handler(self, handler):
        self._accepted_connections.remove(handler)

    def handle_close(self):
        self.log.info("Shutting down server, closing all remaining client connections.")

        for handler in self._accepted_connections:
            handler.close()
        self._accepted_connections = []
        self.close()


class ModbusAdapter(Adapter):
    default_options = {"bind_address": "0.0.0.0", "port": 502}

    def __init__(self, options=None):
        super(ModbusAdapter, self).__init__(options)
        self._server = None

    def start_server(self):
        self._server = ModbusServer(
            self._options.bind_address,
            self._options.port,
            self.interface,
            self.device_lock,
        )

    def stop_server(self):
        if self._server is not None:
            self._server.close()
            self._server = None

    @property
    def is_running(self):
        return self._server is not None

    def handle(self, cycle_delay=0.1):
        asyncore.loop(cycle_delay, count=1)


class ModbusInterface(InterfaceBase):
    protocol = "modbus"
    di = None
    co = None
    ir = None
    hr = None

    @property
    def adapter(self):
        return ModbusAdapter
