from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, AliasProperty
from kivy.event import EventDispatcher
import serial
from serial.tools.list_ports_common import ListPortInfo
from enum import Enum, auto
from typing import Optional
import time
import queue
from libs.properties import EnumProperty
from libs import logger


class SerialState(Enum):
    CONNECTED = auto()  # устройство подключено и готово к записи
    TRY_CONNECT = auto()  # подключение...
    WAIT_INIT = auto()  # ожидание ответа об инициализации устройства
    OFF = auto()  # соединение отключено
    DISCONNECTED = auto()  # соединение разорвано во время использования


class SerialDevice(EventDispatcher):
    port_info: ListPortInfo = ObjectProperty()
    product_name = StringProperty(allownone=True)
    _state = EnumProperty(SerialState, SerialState.OFF, rebind=True)
    device: Optional[serial.Serial] = ObjectProperty(allownone=True)
    handshake_msg = ObjectProperty(None, allownone=True)  # bytes
    handshake_ack = ObjectProperty(None, allownone=True)  # bytes (one)
    is_send_terminate_message = BooleanProperty(False)

    HANDSHAKE_ACK_SETTLE_TIME = 0.05
    _connection_down_time = None
    _wait_handshake_time_start = None
    _prev_handshake_time_send = None
    def __init__(self, baudrate: int, try_connection_time: float=5.0, **kwargs):
        self.baudrate = baudrate
        self.try_connection_time = try_connection_time
        self._command_queue = queue.Queue()
        super().__init__(**kwargs)

    def _set_state(self, state: SerialState):
        logger.info(f"_set_state: прошлый={self._state}, новый={state}")
        old_state = self._state
        if old_state is state:
            return False
        if old_state is SerialState.CONNECTED and state is SerialState.TRY_CONNECT:
            return False

        if old_state is SerialState.CONNECTED and state is not SerialState.DISCONNECTED:
            if self.is_send_terminate_message and self.device:
                try:
                    self._write(self._get_terminate_message())
                    self._read(self.device.in_waiting)
                except (serial.SerialException, OSError):
                    logger.warning("Не удалось отправить terminate-сообщение", exc_info=True)
            self._close_device()

        if state is SerialState.CONNECTED:
            logger.info("Соединение произошло успешно")
        self._state = state
        return True
    state = AliasProperty(lambda self: self._state, _set_state, rebind=True)

    def close_connection(self):
        def _close_connection_command():
            self.state = SerialState.OFF
        self._command_queue.put(_close_connection_command)

    def connect(self):
        def _connect_command():
            self.state = SerialState.TRY_CONNECT
        self._command_queue.put(_connect_command)

    def write(self, data: bytes):
        def _write_command():
            self._write_direct(data)
        self._command_queue.put(_write_command)

    def loop(self):
        while not self._command_queue.empty():
            self._command_queue.get()()

        if self.state is SerialState.WAIT_INIT:
            self._check_wait_init()

        self._check_connection_down_time()
        self._check_for_incoming_data()
        self._try_connect()

    def _check_wait_init(self):
        if self._wait_device_handshake_msg() not in (True, None):
            self._close_device()
            self.state = SerialState.OFF
            logger.warning("Таймаут ожидания handshake")

    def _try_connect(self):
        if self.state in (SerialState.TRY_CONNECT, SerialState.DISCONNECTED):
            logger.info("Попытка подключения")
            if self.device:
                self._close_device()
            device = self._connect_to_device()
            if not device:
                return
            if self.handshake_msg:
                self.state = SerialState.WAIT_INIT
                self.device = device
                device.reset_input_buffer()
                self._wait_handshake_time_start = time.monotonic()
                self._prev_handshake_time_send = None
            else:
                self.device = device
                self.state = SerialState.CONNECTED

    # Это режим "контроллер отправляет, хост слушает"
    # def _wait_device_handshake_msg(self) -> bool:
    #     device = self.device
    #     if (time.monotonic() - self._wait_handshake_time_start) >= self.try_connection_time:
    #         return False
    #     try:
    #         if device.in_waiting >= len(self.handshake_msg):
    #             msg = device.read(len(self.handshake_msg))
    #             if msg == self.handshake_msg:
    #                 logger.info(f"Принят handshake. Отправка в ответ {self.handshake_msg}. Ждем {self.HANDSHAKE_ACK_SETTLE_TIME}, device.in_waiting={device.in_waiting}")
    #                 device.write(self.handshake_msg)
    #                 time.sleep(self.HANDSHAKE_ACK_SETTLE_TIME)
    #                 logger.info(f"Очищаем input_buffer. Сейчас device.in_waiting={device.in_waiting}")
    #                 device.reset_input_buffer()
    #                 logger.info(f"После очистки device.in_waiting={device.in_waiting}. Ждем еще 0.05с")
    #                 time.sleep(0.05)
    #                 logger.info(f"Второй раз очищаем input_buffer. Сейчас device.in_waiting={device.in_waiting}")
    #                 device.reset_input_buffer()
    #                 logger.info(f"После второго раза очистки device.in_waiting={device.in_waiting}")
    #                 self.state = SerialState.CONNECTED
    #         return True
    #     except (serial.SerialException, OSError):
    #         logger.error("Ошибка handshake", exc_info=True)
    #         return False

    # Это режим "хост отправляет, контроллер слушает"
    def _wait_device_handshake_msg(self) -> Optional[bool]:
        device = self.device
        if (time.monotonic() - self._wait_handshake_time_start) >= self.try_connection_time:
            return False
        try:
            # time.sleep(self.HANDSHAKE_ACK_SETTLE_TIME)
            if device.in_waiting < len(self.handshake_msg):
                if not self._prev_handshake_time_send or (time.monotonic() - self._prev_handshake_time_send) >= self.HANDSHAKE_ACK_SETTLE_TIME:
                    logger.info(f"Отправляем handshake {self.handshake_msg}. device.in_waiting={device.in_waiting}")
                    device.write(self.handshake_msg)
                    self._prev_handshake_time_send = time.monotonic()
                return None
            msg = device.read(len(self.handshake_msg))
            # if msg != self.handshake_msg:
            #     logger.info(f"Пришел неверный handshake {msg}. device.in_waiting={device.in_waiting}")
            #     device.reset_input_buffer()
            #     return None
            logger.info(f"Пришел ответный handshake {msg}")
            self.state = SerialState.CONNECTED
            return True
        except (serial.SerialException, OSError):
            logger.error("Ошибка handshake", exc_info=True)
            return False

    def _connect_to_device(self) -> Optional[serial.Serial]:
        try:
            return self._create_serial_device()
        except serial.SerialException:
            return None

    def _create_serial_device(self) -> Optional[serial.Serial]:
        return serial.Serial(
            self.port_info.device,
            self.baudrate
        )

    def _check_for_incoming_data(self):
        if self._is_connected():
            try:
                self._process_pending_input()
            except (serial.SerialException, ValueError):
                logger.error("Ошибка чтения сообщения serial", exc_info=True)
                self._lost_connection()
            except OSError as e:
                logger.error(f"Serial I/O error (скорее всего кабель отключен)", exc_info=True)
                self._lost_connection()

    def _process_pending_input(self):
        pass

    def _lost_connection(self):
        self._close_device()
        self.state = SerialState.DISCONNECTED
        self._connection_down_time = time.monotonic()
        while True:
            try:
                self._command_queue.get_nowait()
            except queue.Empty:
                break

    def _is_connected(self) -> bool:
        return self.device and self.device.is_open and self.state is SerialState.CONNECTED

    def _check_connection_down_time(self):
        if self.state is SerialState.DISCONNECTED and\
            ((time.monotonic() - self._connection_down_time) > self.try_connection_time):
            self.state = SerialState.OFF
            self._connection_down_time = None

    def _write_direct(self, data: bytes) -> bool:
        if not self._is_connected():
            logger.warning("Попытка записи в неподключённое устройство")
            return False
        try:
            self._write(data)
            return True
        except serial.SerialException:
            logger.error(f"SerialException while write to device {data}", exc_info=True)
            self._lost_connection()
            return False
        except OSError as e:
            logger.error(f"Serial I/O error", exc_info=True)
            self._lost_connection()
            return False

    def _write(self, data: bytes):
        self.device.write(data)

    def _read(self, count: int) -> Optional[bytes]:
        if not self._is_connected():
            logger.warning("Попытка чтения из неподключенного устройства")
            return None
        try:
            return self.device.read(count)
        except (serial.SerialException, OSError):
            logger.warning("Ошибка чтения", exc_info=True)
            return None

    def _close_device(self):
        try:
            if self.device:
                self.device.close()
            self.device = None
        except serial.SerialException:
            logger.warning("Ошибка закрытия serial порта", exc_info=True)

    def _get_terminate_message(self) -> bytes:
        raise NotImplementedError

    def matches_port(self, other_port_info: ListPortInfo) -> bool:
        port_info = self.port_info
        return (port_info.serial_number == other_port_info.serial_number) and\
               (port_info.manufacturer == other_port_info.manufacturer) and\
               (port_info.product == other_port_info.product) and\
               (port_info.interface == other_port_info.interface)

    def __repr__(self) -> str:
        p = self.port_info
        return f"(serial_number: {p.serial_number}, "\
               f"manufacturer: {p.manufacturer}, "\
               f"product: {p.product}, "\
               f"interface: {p.interface}, "\
               f"product_name: {self.product_name})"
