import queue
import time
from enum import Enum, auto
from typing import Any, Callable, List, Optional, Set, Tuple

from kivy.event import EventDispatcher
from kivy.properties import (
    AliasProperty,
    ListProperty,
    NumericProperty,
    StringProperty,
)

from libs import logger
from libs.properties import EnumProperty
from libs.utils import ThrottledCall


class Device(EventDispatcher):
    """Базовое устройство. Пассивное: дренирование очереди и работу с
    протоколом делает кто-то снаружи через check_messages()"""
    name: str = StringProperty("")

    _SIGNAL_MISSING = "missing"
    _SIGNAL_PRESENT = "present"
    _SIGNAL_CONNECT = "connect"
    _SIGNAL_CLOSE = "close"

    _command_queue: "queue.Queue[Callable[[], None]]"
    _last_signal: Optional[str]

    def __init__(self, **kwargs: Any):
        self._command_queue = queue.Queue()
        self._last_signal = None
        super().__init__(**kwargs)

    # --- публичный API для observer'а ---

    def matches_port(self, port: Any) -> bool:
        raise NotImplementedError()

    def can_be_removed(self) -> bool:
        """True, если observer может удалить устройство из списка."""
        return False

    def notify_missing(self) -> None:
        """Observer: порт больше не в списке."""
        self._push_signal(self._SIGNAL_MISSING)

    def notify_present(self) -> None:
        """Observer: порт снова в списке."""
        self._push_signal(self._SIGNAL_PRESENT)

    # --- публичный API для владельца (event_thread) или UI ---

    def connect(self) -> None:
        self._push_signal(self._SIGNAL_CONNECT)

    def close_connection(self) -> None:
        self._push_signal(self._SIGNAL_CLOSE)

    def _close_resource(self) -> None:
        raise NotImplementedError()

    def check_messages(self) -> None:
        """Точка входа. Дренирует очередь + делает работу с протоколом.
        Наследник НЕ переопределяет этот метод, только _on_check_messages."""
        self._drain_queue()
        self._on_check_messages()

    def is_connected(self) -> bool:
        """Для UI и логики потребителя. Observer это не использует."""
        raise NotImplementedError()

    # --- хуки для наследников ---

    def _do_connect(self) -> None:
        raise NotImplementedError()

    def _do_close_connection(self) -> None:
        raise NotImplementedError()

    def _on_check_messages(self) -> None:
        """Работа с протоколом. Переопределяется наследником."""
        pass

    def _handle_missing(self) -> None:
        """Реакция на notify_missing. Переопределяется наследником."""
        pass

    def _handle_present(self) -> None:
        """Реакция на notify_present. Переопределяется наследником."""
        pass

    # --- внутреннее ---

    def _drain_queue(self) -> None:
        while True:
            try:
                cmd = self._command_queue.get_nowait()
            except queue.Empty:
                break
            try:
                cmd()
            except Exception:
                logger.error(f"Device [{self.name}]: command failed", exc_info=True)
        self._last_signal = None

    def _push_action(self, callback: Callable[[], None]):
        self._command_queue.put(callback)

    def _push_signal(self, signal: str) -> None:
        self._command_queue.put(lambda: self._on_signal(signal))

    def _on_signal(self, signal: str) -> None:
        if self._last_signal == signal:
            return
        self._last_signal = signal
        if signal == self._SIGNAL_MISSING:
            self._handle_missing()
        elif signal == self._SIGNAL_PRESENT:
            self._handle_present()
        elif signal == self._SIGNAL_CONNECT:
            self._do_connect()
        elif signal == self._SIGNAL_CLOSE:
            self._do_close_connection()
        else:
            logger.warning(f"Device [{self.name}]: unknown signal {signal!r}")


class ConnectionState(Enum):
    OFF = auto()
    TRY_CONNECT = auto()
    WAIT_INIT = auto()
    CONNECTED = auto()
    DISCONNECTED = auto()


class StatefulDevice(Device):
    """Устройство с состояниями подключения и grace-периодом."""

    _state: ConnectionState = EnumProperty(
        ConnectionState, ConnectionState.OFF, rebind=True
    )

    def __init__(
            self,
            try_connection_time: float,
            **kwargs: Any
        ):
        self._connection_down_time: Optional[float] = None
        self.try_connection_time = try_connection_time
        super().__init__(**kwargs)

    def set_state(self, new_state: ConnectionState) -> bool:
        if self._state is new_state:
            return False
        logger.info(
            f"{type(self).__name__} [{self.name}]: state changed {self._state} -> {new_state}"
        )
        self._state = new_state
        return True

    state = AliasProperty(lambda self: self._state, set_state, bind=("_state",))

    # --- интерфейс для observer'а ---

    def can_be_removed(self) -> bool:
        return self._state is ConnectionState.OFF

    def is_connected(self) -> bool:
        return self._state is ConnectionState.CONNECTED

    # --- реакции на сигналы observer ---

    def _handle_missing(self) -> None:
        if self._state in (ConnectionState.CONNECTED,
                           ConnectionState.TRY_CONNECT,
                           ConnectionState.WAIT_INIT):
            self._close_resource()
            self.state = ConnectionState.DISCONNECTED
            self._connection_down_time = time.monotonic()

    def _handle_present(self) -> None:
        if self._state is ConnectionState.DISCONNECTED:
            self._connection_down_time = None
            self.state = ConnectionState.TRY_CONNECT

    # --- работа в event_thread ---

    def _on_check_messages(self) -> None:
        self._check_connection_down_time()
        if self._state is ConnectionState.WAIT_INIT:
            self._check_wait_init()
        elif self._state in (ConnectionState.TRY_CONNECT,
                             ConnectionState.DISCONNECTED):
            self._try_connect()
        if self._state is ConnectionState.CONNECTED:
            self._read_messages()

    def _check_connection_down_time(self) -> None:
        if (self._state is ConnectionState.DISCONNECTED
                and self._connection_down_time is not None
                and time.monotonic() - self._connection_down_time
                    > self.try_connection_time):
            self.state = ConnectionState.OFF
            self._connection_down_time = None

    def _try_connect(self) -> None:
        if self._has_connection():
            return
        try:
            self._open_connection()
        except Exception:
            logger.warning(
                f"{type(self).__name__} [{self.name}]: connect failed",
                exc_info=True,
            )

    def _check_wait_init(self) -> None:
        """Для устройств с handshake. По умолчанию — переход в CONNECTED."""
        self.state = ConnectionState.CONNECTED

    def _lost_connection(self) -> None:
        self._close_resource()
        if self._state in (ConnectionState.CONNECTED,
                           ConnectionState.WAIT_INIT):
            self.state = ConnectionState.DISCONNECTED
            self._connection_down_time = time.monotonic()

    # --- внутренние команды из очереди ---

    def _do_connect(self) -> None:
        if self._state in (ConnectionState.TRY_CONNECT,
                           ConnectionState.WAIT_INIT,
                           ConnectionState.CONNECTED):
            return
        self._connection_down_time = None
        self.state = ConnectionState.TRY_CONNECT

    def _do_close_connection(self) -> None:
        if self._state is ConnectionState.OFF:
            return
        self._close_resource()
        self.state = ConnectionState.OFF
        self._connection_down_time = None

    # --- хуки для наследников ---

    def _has_connection(self) -> bool:
        """Есть ли уже открытое соединение."""
        raise NotImplementedError()

    def _open_connection(self) -> None:
        """Открыть ресурс. При успехе выставить state
        (CONNECTED или WAIT_INIT)."""
        raise NotImplementedError()

    def _read_messages(self) -> None:
        """Читать данные. Переопределяется наследником."""
        raise NotImplementedError()


class DeviceObserver(EventDispatcher):
    name: str

    devices: Tuple[Device, ...] = ListProperty()
    monitoring_interval: float = NumericProperty(1)

    __events__ = ("on_new_device", "on_remove_device")

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.throttled_monitor_connection = ThrottledCall(
            self.monitor_connections,
            self.monitoring_interval
        )

    def on_new_device(self, device: Device):
        logger.info(f"Observer [{self.name}]: new device {device}")

    def on_remove_device(self, device: Device):
        logger.info(f"Observer [{self.name}]: remove device {device}")

    def on_monitoring_interval(self, _, interval: float):
        if self.throttled_monitor_connection:
            self.throttled_monitor_connection.interval = interval

    def monitor_connections(self) -> None:
        self._monitor_connections()

    def _get_ports(self) -> List[Any]:
        """Список ключей, которые observer считает 'сейчас присутствующими'."""
        raise NotImplementedError()

    def _make_device(self, port: Any) -> Device:
        """Создать устройство по ключу."""
        raise NotImplementedError()

    # --- основной цикл ---

    def _monitor_connections(self) -> None:
        ports = self._get_ports()

        matched_devices: Set[int] = set()      # индексы в self.devices
        matched_ports: Set[int] = set()   # индексы в ports

        # 1. Сопоставить существующие устройства с кандидатами
        for ci, port in enumerate(ports):
            for di, device in enumerate(self.devices):
                if di in matched_devices:
                    continue
                if device.matches_port(port):
                    device.notify_present()
                    matched_devices.add(di)
                    matched_ports.add(ci)
                    break

        # 2. Уведомить тех, кому кандидата не нашлось
        for di, device in enumerate(self.devices):
            if di not in matched_devices:
                device.notify_missing()

        # 3. Создать новые для непарных кандидатов
        new_devices = [
            self._make_device(c)
            for ci, c in enumerate(ports)
            if ci not in matched_ports
        ]

        # 4. Удалять только тех, кто и не в кандидатах, и готов уйти
        to_remove = [
            d for di, d in enumerate(self.devices)
            if di not in matched_devices and d.can_be_removed()
        ]

        # 5. Одно присваивание — одно событие для UI
        if new_devices or to_remove:
            removed_ids = {id(d) for d in to_remove}
            remaining = tuple(
                d for d in self.devices if id(d) not in removed_ids
            ) + tuple(new_devices)
            self.devices = remaining

        # 6. События
        for d in new_devices:
            self.dispatch("on_new_device", d)
        for d in to_remove:
            self.dispatch("on_remove_device", d)
