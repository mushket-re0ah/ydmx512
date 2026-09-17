from kivy.properties import ObjectProperty, NumericProperty, StringProperty
from serial.tools.list_ports_common import ListPortInfo
from libs.serial.device import SerialState, SerialDevice
from .. import message
import serial
import time
from enum import IntEnum
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DMXResultCode(IntEnum):
    SUCCESS = 0x00
    TERMINATE_CONNECTION = 0x01
    UNCORRECT_MSG_SIZE = 0x02
    UNCORRECT_MSG_TYPE = 0x03
    UNCORRECT_ADDRESS = 0x04
    READ_ERROR = 0x05
    READ_COUNT_ERROR = 0x06
    ADDRESS_LENGHT_ERROR = 0x07
    CRC_ERROR = 0x08
    WATCHDOG_ERROR = 0x09
    IDENTIFY = 0x10


class DMXSerialDevice(SerialDevice):
    universe = NumericProperty()

    def __init__(self, **kwargs):
        from .. import dmx512
        self._timeout = dmx512.SERIAL_TIMEOUT
        super().__init__(
            baudrate=dmx512.SERIAL_BAUDRATE,
            try_connection_time=dmx512.SERIAL_TRY_CONNECTION_TIME,
            handshake_msg=dmx512.DMX_HELLO_MSG,
            handshake_ack=bytes([DMXResultCode.SUCCESS]),
            is_send_terminate_message=True,
            universe=dmx512.get_free_universe(),
            **kwargs
        )

    def on_universe(self, _, universe: int):
        from .. import dmx512
        dmx512.trigger_sync_universe_device()

    def _create_serial_device(self) -> serial.Serial:
        return serial.Serial(
            self.port_info.device,
            self.baudrate,
            timeout=self._timeout
        )

    def _get_terminate_message(self) -> bytes:
        return message.create_terminate_connection_message()

    def _process_pending_input(self):
        from .. import dmx512
        if self.device.in_waiting > 0:
            raw = self.device.read(1)
            if not raw:
                return
            pending_code = int.from_bytes(raw, byteorder=dmx512.DMX_MESSAGE_BYTEORDER)
            try:
                code = DMXResultCode(pending_code)
            except ValueError:
                logger.warning(f"Неизвестный код сообщения: {pending_code:#x}, device.in_waiting={self.device.in_waiting}")
                self.device.reset_input_buffer()
                return
            if code == DMXResultCode.WATCHDOG_ERROR:
                logger.warning("WATCHDOG_ERROR в _process_pending_input! Перезагрузка прошивки прошла успешно...")
                self.device.reset_input_buffer()
                # Соединение не потеряно
                # self._lost_connection()
            else:
                logger.warning(f"Внезапное сообщение в _process_pending_input: {code.name}")
                self.device.reset_input_buffer()

    def _write(self, data: bytes):
        from .. import dmx512
        self.device.write(data)
        raw = self.device.read(1)
        if not raw:
            raise serial.SerialException("Пустой ответ от устройства")
        end_msg = int.from_bytes(raw, byteorder=dmx512.DMX_MESSAGE_BYTEORDER)
        try:
            exit_code = DMXResultCode(end_msg)
        except ValueError:
            raise ValueError(f"end_msg={end_msg:#x}, не является известным кодом, msg={data, str(data)}, msg_len={len(data)}")
        if exit_code != DMXResultCode.SUCCESS:
            if exit_code == DMXResultCode.TERMINATE_CONNECTION:
                logger.info("Соединение завершено корректно")
            else:
                logger.warning(f"end_msg={exit_code.name} (0x{exit_code.value:02X}), msg={data}, msg_len={len(data)}")
        if exit_code == DMXResultCode.WATCHDOG_ERROR:
            logger.error("WATCHDOG_ERROR после записи! Перезагрузка прошивки...")
            raise serial.SerialException("WATCHDOG_ERROR")

    def __repr__(self) -> str:
        p = self.port_info
        return f"(serial_number: {p.serial_number}, "\
               f"manufacturer: {p.manufacturer}, "\
               f"product: {p.product}, "\
               f"interface: {p.interface}, "\
               f"universe: {self.universe}, "\
               f"product_name: {self.product_name})"
