#!/usr/bin/env python3

import ctypes
import enum
import logging
import sys
import time

from typing import List, Optional

import usb1


def _error(msg: str, code: int = 1) -> None:
    '''
    Prints an error message and exits. Will color the output when writting to a TTY.
    :param msg: Error message
    :param code: Error code
    '''
    prefix = 'ERROR'
    if sys.stdout.isatty():
        prefix = '\33[91m' + prefix + '\33[0m'
    print('{} {}'.format(prefix, msg))
    exit(code)


class _Request(enum.Enum):
    CONTROL = 1
    REG_READ = 10
    REG_WRITE = 11


class _Registers(enum.Enum):
    SIZE_X = 0x0022
    SIZE_Y = 0x0023


class ScopetekDevice():
    def __init__(self, device: usb1.USBDeviceHandle) -> None:
        self.__logger = logging.getLogger(self.__class__.__name__)
        self._dev = device

    def request(self, request: _Request, index: int, value: int, *,
                data: Optional[List[int]] = None, size: Optional[int] = None,
                timeout: int = 0) -> Optional[List[int]]:
        if request == _Request.CONTROL:
            request_type = 0x40  # host to dev, vendor, dev
            size = 0
        elif request == _Request.REG_READ or request == _Request.REG_WRITE:
            request_type = 0xc0  # dev to host, vendor, dev
            if size is None:
                size = 1
        else:
            raise TypeError('Unknown request')

        # https://github.com/python/mypy/issues/9264
        buffer = bytearray(data if data else size)  # type: ignore

        if data:
            self.__logger.debug('write(0x{:04x}, 0x{:04x}) {}'.format(
                index, value, ''.join(f'{byte:02x}' for byte in data)
            ))
        else:
            self.__logger.debug(f' send(0x{index:04x}, 0x{value:04x})')

        # https://github.com/vpelletier/python-libusb1/issues/56
        buffer, _ = usb1.create_initialised_buffer(buffer)
        self._dev._controlTransfer(
            request_type,
            request.value,
            value,
            index,
            buffer,
            ctypes.sizeof(buffer),
            timeout
        )
        time.sleep(0.002)

        if buffer:
            data = [int.from_bytes(byte, byteorder='big') for byte in buffer]
            self.__logger.debug(' read(0x{:04x}, 0x{:04x}) {}'.format(
                index, value, ''.join(f'{byte:02x}' for byte in data)
            ))

            if data[-1] != 0x08:
                raise RuntimeError(f'Received error from the device: {data[-1]}')

            return data

        return None


def main() -> None:
    ctx = usb1.LibUSBContext()
    usb_dev = ctx.openByVendorIDAndProductID(0x0547, 0x4d33)

    if not usb_dev:
        _error('Device not found (0x0547, 0x4d33)')

    dev = ScopetekDevice(usb_dev)

    dev.request(_Request.CONTROL, 0x000f, 0x0001)
    dev.request(_Request.CONTROL, 0x000f, 0x0000)  # stop
    dev.request(_Request.CONTROL, 0x000f, 0x0001)

    dev.request(_Request.REG_READ, 0x0000, 0x0000, size=3)

    dev.request(_Request.REG_WRITE, 0x000a, 0x8000)
    dev.request(_Request.REG_WRITE, 0x000d, 0x0001)
    dev.request(_Request.REG_WRITE, 0x000d, 0x0000)

    time.sleep(1)

    dev.request(_Request.REG_WRITE, 0x0001, 0x0015)  # X?
    dev.request(_Request.REG_WRITE, 0x0002, 0x0021)  # Y?

    dev.request(_Request.REG_WRITE, 0x0020, 0x0000)
    dev.request(_Request.REG_WRITE, 0x001e, 0x8040)
    dev.request(_Request.REG_WRITE, 0x004e, 0x0030)

    dev.request(_Request.REG_WRITE, 0x0004, 0x07ff)  # X?
    dev.request(_Request.REG_WRITE, 0x0003, 0x05ff)  # Y?

    dev.request(_Request.REG_WRITE, 0x002b, 0x0060)
    dev.request(_Request.REG_WRITE, 0x002c, 0x0060)
    dev.request(_Request.REG_WRITE, 0x002d, 0x0060)
    dev.request(_Request.REG_WRITE, 0x002e, 0x0060)

    dev.request(_Request.REG_WRITE, 0x000a, 0x8001)

    dev.request(_Request.REG_WRITE, 0x0022, 0x0033)
    dev.request(_Request.REG_WRITE, 0x0023, 0x0033)

    dev.request(_Request.REG_WRITE, 0x0005, 0x0150)
    dev.request(_Request.REG_WRITE, 0x000a, 0x8000)
    dev.request(_Request.REG_WRITE, 0x0005, 0x0300)

    dev.request(_Request.REG_READ, 0x0005, 0x0000, size=3)
    dev.request(_Request.REG_READ, 0x0004, 0x0000, size=3)
    dev.request(_Request.REG_READ, 0x0002, 0x0000, size=3)

    dev.request(_Request.REG_WRITE, 0x0009, 0x012c)
    dev.request(_Request.REG_WRITE, 0x0035, 0x0056)

    dev.request(_Request.CONTROL, 0x000f, 0x0003)


if __name__ == '__main__':
    if '--debug' in sys.argv[1:]:
        logging.basicConfig(level=logging.DEBUG)

    main()
