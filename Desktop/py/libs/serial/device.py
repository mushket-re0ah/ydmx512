import queue
import time
from typing import Any, Optional

import serial
from kivy.properties import (
    BooleanProperty,
    ObjectProperty,
    StringProperty,
)
from serial.tools.list_ports_common import ListPortInfo

from libs import logger
from libs.device_observer import ConnectionState, StatefulDevice


class SerialDevice(StatefulDevice):
    port_info: ListPortInfo = ObjectProperty()
    product_name: Optional[str] = StringProperty(allownone=True)
    device: Optional[serial.Serial] = ObjectProperty(allownone=True)
    handshake_msg: Optional[bytes] = ObjectProperty(None, allownone=True)
    handshake_ack: Optional[bytes] = ObjectProperty(None, allownone=True)
    is_send_terminate_message: bool = BooleanProperty(False)

    HANDSHAKE_ACK_SETTLE_TIME: float = 0.05

    def __init__(
            self,
            port_info: ListPortInfo,
            product_name: Optional[str],
            baudrate: int = 115200,
            try_connection_time: float = 5.0,
            **kwargs: Any
        ):
        if product_name is not None:
            self.name = product_name
        self.port_info = port_info
        self.product_name = product_name
        self.baudrate = baudrate
        self._wait_handshake_time_start: float = 0.0
        self._prev_handshake_time_send: Optional[float] = None
        super().__init__(
            try_connection_time=try_connection_time,
            **kwargs,
        )

    # --- интерфейс для observer'а ---

    def matches_port(self, port_info: ListPortInfo) -> bool:  # pyright: ignore[reportIncompatibleMethodOverride]
        p = self.port_info
        return (p.serial_number == port_info.serial_number and
                p.manufacturer == port_info.manufacturer and
                p.product == port_info.product and
                p.interface == port_info.interface)

    # --- публичный API ---

    def is_connected(self) -> bool:
        return (
            self.device is not None
            and self.device.is_open
            and self._state is ConnectionState.CONNECTED
        )

    def write(self, data: bytes) -> None:
        self._push_action(lambda: self._write_direct(data))

    # --- StatefulDevice hooks ---

    def _has_connection(self) -> bool:
        return self.device is not None and self.device.is_open

    def _open_connection(self) -> None:
        device = self._create_serial_device()
        self.device = device
        if self.handshake_msg:
            device.reset_input_buffer()
            self._wait_handshake_time_start = time.monotonic()
            self._prev_handshake_time_send = None
            self.state = ConnectionState.WAIT_INIT
        else:
            self.state = ConnectionState.CONNECTED

    def _check_wait_init(self) -> None:
        result = self._wait_device_handshake_msg()
        if result is False:
            self._close_resource()
            self.state = ConnectionState.OFF
            logger.warning(f"SerialDevice [{self.name}]: Таймаут ожидания handshake")

    def _read_messages(self) -> None:
        try:
            self._process_pending_input()
        except (serial.SerialException, OSError):
            logger.error(f"SerialDevice [{self.name}]: связь потеряна, закрываю порт")
            self._lost_connection()
        except ValueError:
            logger.error(f"SerialDevice [{self.name}]: read failed", exc_info=True)
            self._lost_connection()

    def _close_resource(self) -> None:
        try:
            if self.device:
                self.device.close()
        except serial.SerialException:
            logger.warning(
                f"SerialDevice [{self.name}]: Ошибка закрытия serial порта", exc_info=True
            )
        finally:
            self.device = None

    def _do_close_connection(self) -> None:
        if (self._state is ConnectionState.CONNECTED
                and self.is_send_terminate_message
                and self.device is not None):
            self._send_terminate_message()
        super()._do_close_connection()

    def _on_lost_connection(self) -> None:
        while True:
            try:
                self._command_queue.get_nowait()
            except queue.Empty:
                break

    # --- хуки для наследников ---

    def _create_serial_device(self) -> serial.Serial:
        raise NotImplementedError()

    def _get_terminate_message(self) -> bytes:
        raise NotImplementedError()

    def _process_pending_input(self) -> None:
        """Читать и обрабатывать входящие данные. Переопределяется наследником."""
        pass

    # --- handshake ---

    def _wait_device_handshake_msg(self) -> Optional[bool]:
        device = self.device
        if device is None:
            raise ValueError("device is None")
        if self.handshake_msg is None:
            raise ValueError("handshake_msg is None")
        if time.monotonic() - self._wait_handshake_time_start >= self.try_connection_time:
            return False
        try:
            if device.in_waiting < len(self.handshake_msg):
                if (self._prev_handshake_time_send is None
                        or time.monotonic() - self._prev_handshake_time_send
                            >= self.HANDSHAKE_ACK_SETTLE_TIME):
                    logger.info(
                        f"SerialDevice [{self.name}]: Отправляем handshake {self.handshake_msg}"
                    )
                    device.write(self.handshake_msg)
                    self._prev_handshake_time_send = time.monotonic()
                return None
            msg = device.read(len(self.handshake_msg))
            logger.info(f"SerialDevice [{self.name}]: Пришел ответный handshake {msg}")
            self.state = ConnectionState.CONNECTED
            return True
        except (serial.SerialException, OSError):
            logger.error(f"SerialDevice [{self.name}]: Ошибка handshake", exc_info=True)
            return False

    # --- terminate ---

    def _send_terminate_message(self) -> None:
        try:
            self._write(self._get_terminate_message())
            if self.device is not None:
                self._read(self.device.in_waiting)
        except (serial.SerialException, OSError):
            logger.warning(
                f"SerialDevice [{self.name}]: Не удалось отправить terminate-сообщение",
                exc_info=True
            )

    # --- низкоуровневое I/O ---

    def _write_direct(self, data: bytes) -> bool:
        if not self.is_connected():
            logger.warning(
                f"SerialDevice [{self.name}]: Попытка записи в неподключённое устройство"
            )
            return False
        try:
            self._write(data)
            return True
        except serial.SerialException:
            logger.error(
                f"SerialDevice [{self.name}]: "\
                f"SerialException while write to device {data}",
                exc_info=True
            )
            self._lost_connection()
            return False
        except OSError:
            logger.error(f"SerialDevice [{self.name}]: Serial I/O error", exc_info=True)
            self._lost_connection()
            return False

    def _write(self, data: bytes) -> None:
        if self.device is None:
            logger.warning(
                f"SerialDevice [{self.name}]: Попытка записи в неподключенное устройство"
            )
            return
        self.device.write(data)

    def _read(self, count: int) -> Optional[bytes]:
        if self.device is None:
            logger.warning(
                f"SerialDevice [{self.name}]: Попытка чтения из неподключенного устройства"
            )
            return None
        try:
            return self.device.read(count)
        except (serial.SerialException, OSError):
            logger.warning(f"SerialDevice [{self.name}]: Ошибка чтения", exc_info=True)
            return None

    def __repr__(self) -> str:
        p = self.port_info
        return (f"SerialDevice(serial_number: {p.serial_number}, "
                f"manufacturer: {p.manufacturer}, "
                f"interface: {p.interface}, "
                f"product_name: {self.product_name})")
