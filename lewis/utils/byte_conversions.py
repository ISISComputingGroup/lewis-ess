import struct

BYTE = 2**8


def _get_byteorder_name(low_byte_first):
    """
    Get the python name for low byte first
    :param low_byte_first: True for low byte first; False for MSB first
    :return: name
    """
    return 'little' if low_byte_first else 'big'


def int_to_raw_bytes(integer, length, low_byte_first) -> bytes:
    """
    Converts an integer to an unsigned set of bytes with the specified length (represented as a string). Unless the
    integer is negative in which case it converts to a signed integer.

    If low byte first is True, the least significant byte comes first, otherwise the most significant byte comes first.

    Args:
        integer (int): The integer to convert.
        length (int): The length of the result.
        low_byte_first (bool): Whether to put the least significant byte first.

    Returns:
        string representation of the bytes.
    """
    return integer.to_bytes(length=length, byteorder=_get_byteorder_name(low_byte_first), signed=integer < 0)


def raw_bytes_to_int(raw_bytes, low_bytes_first=True):
    """
    Converts an unsigned set of bytes to an integer.

    Args:
        raw_bytes (bytes): A string representation of the raw bytes.
        low_bytes_first (bool): Whether the given raw bytes are in little endian or not. True by default.

    Returns:
        int: The integer represented by the raw bytes passed in.
    """
    return int.from_bytes(raw_bytes, byteorder=_get_byteorder_name(low_bytes_first))


def float_to_raw_bytes(real_number: float, low_byte_first: bool = True) -> bytes:
    """
    Converts an floating point number to an unsigned set of bytes.

    Args:
        real_number: The float to convert.
        low_byte_first: Whether to put the least significant byte first. True by default.

    Returns:
        A string representation of the bytes.
    """
    raw_bytes = bytes(struct.pack(">f", real_number))

    return raw_bytes[::-1] if low_byte_first else raw_bytes


def raw_bytes_to_float(raw_bytes):
    """
    Convert a set of bytes to a floating point number

    Args:
        raw_bytes (bytes): A string representation of the raw bytes.

    Returns:
        float: The floating point number represented by the given bytes.
    """
    return struct.unpack('f', raw_bytes[::-1])[0]
