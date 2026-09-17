from typing import List
from enum import Enum


def to_bytes(value: int, length: int) -> bytes:
    from . import dmx512
    return value.to_bytes(length=length, byteorder=dmx512.DMX_MESSAGE_BYTEORDER, signed=False)


class MessageType(int, Enum):
    TERMINATE_CONNECTION = 0x00
    STANDARD = 0x01
    ADDRESS_COMPRESS = 0x02
    ADDRESS_VALUES_COMPRESS = 0x03
    START_CONNECTION = 0x04


def _crc8(data: bytes, poly: int = 0x07) -> int:
    """
    Вычисление CRC-8 от данных.
    poly: полином (по умолчанию 0x07 для CRC-8-CCITT).
    """
    crc = 0x00
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
            crc &= 0xFF
    return crc


def _make_metadata(
        message_type: MessageType,
        is_address_1_byte: bool,
        message_size: int) -> bytes:
    """
    Битовая структура заголовка:
    - Байт 0: CRC-8 от байтов 1-2
    - Байт 1 (младший): Биты 7-0 (часть размера)
    - Байт 2 (старший): Биты 15-8 (тип + флаг + часть размера)
    """
    is_address_1_byte = 1 if is_address_1_byte else 0
    metadata_int = ((message_type.value & 0x0F) << 12) | (is_address_1_byte << 11) | message_size
    metadata_bytes = to_bytes(metadata_int, 2)

    crc = _crc8(metadata_bytes)
    crc_byte = bytes([crc])

    return crc_byte + metadata_bytes


def _create_message_standard(
        address_list: List[int],
        value_list: List[int],
        is_address_1_byte: bool) -> bytes:
    data = bytearray()
    addr_size = 1 if is_address_1_byte else 2
    for address, value in zip(address_list, value_list):
        data.extend(to_bytes(address, addr_size))
        data.extend(to_bytes(value, 1))
    return data


def _group_sequential_addresses(address_list: List[int]) -> List[List[int]]:
    """
        Группирует адреса в последовательные блоки.
    """
    groups = []
    current_group = []

    for addr in address_list:
        if not current_group:
            current_group.append(addr)
        elif addr == current_group[-1] + 1:
            current_group.append(addr)
        else:
            groups.append(current_group)
            current_group = [addr]
    if current_group:
        groups.append(current_group)

    return groups


def _group_values_in_block(values: List[int]) -> List[List[int]]:
    """
        Группирует значения внутри одного блока адресов.
    """
    groups = []
    if not values:
        return groups

    current_value = values[0]
    count = 1

    for value in values[1:]:
        if value == current_value:
            count += 1
        else:
            groups.append([count, current_value])
            current_value = value
            count = 1
    groups.append([count, current_value])

    return groups


def _create_message_address_compress(
        address_list: List[int],
        value_list: List[int],
        is_address_1_byte: bool) -> bytes:
    addr_size = 1 if is_address_1_byte else 2

    data = bytearray()
    current_value_index = 0
    for group in _group_sequential_addresses(address_list):
        start_addr = group[0]
        count = len(group)

        values = value_list[current_value_index:current_value_index + count]
        current_value_index += count

        data.extend(to_bytes(count, addr_size))
        data.extend(to_bytes(start_addr, addr_size))
        data.extend(values)
    return data


def _create_message_address_values_compress(
        address_list: List[int],
        value_list: List[int],
        is_address_1_byte: bool) -> bytearray:
    addr_size = 1 if is_address_1_byte else 2

    data = bytearray()
    value_index = 0
    for group in _group_sequential_addresses(address_list):
        start_addr = group[0]
        address_length = len(group)

        group_values = value_list[value_index:value_index + address_length]
        value_index += address_length

        value_blocks = _group_values_in_block(group_values)

        data.extend(to_bytes(address_length, addr_size))
        data.extend(to_bytes(start_addr, addr_size))
        for count, value in value_blocks:
            data.extend(to_bytes(count, addr_size))
            data.append(value)
    return data


def create_message(address_list: List[int], value_list: List[int]) -> bytes:
    if len(address_list) != len(value_list):
        raise ValueError(
            f"address_list по длине не равен value_list, "\
            f"len(address_list)={len(address_list)}, "\
            f"len(value_list)={len(value_list)}")
    if not address_list:
        raise ValueError(f"len(address_list)={len(address_list)}")

    if any((x < 1 or x > 512) for x in address_list):
        raise ValueError(f"адрес находится за пределами DMX512; {address_list}")

    if any((x < 0 or x > 255) for x in value_list):
        raise ValueError(f"значение находится за пределами DMX512; {value_list}")

    is_address_1_byte = all(x <= 255 for x in address_list)

    compressed = [
        (MessageType.STANDARD, _create_message_standard(
                        address_list, value_list, is_address_1_byte)),
        (MessageType.ADDRESS_COMPRESS, _create_message_address_compress(
                        address_list, value_list, is_address_1_byte)),
        (MessageType.ADDRESS_VALUES_COMPRESS, _create_message_address_values_compress(
                        address_list, value_list, is_address_1_byte))
    ]

    message_type, data = min(compressed, key=lambda x: len(x[1]))

    data_size = len(data)
    if data_size > 512 * 3:
        raise ValueError(f"data_size больше 1536, он равен {data_size}")
    return _make_metadata(message_type, is_address_1_byte, data_size) + data


def create_terminate_connection_message() -> bytes:
    return _make_metadata(
        message_type=MessageType.TERMINATE_CONNECTION,
        is_address_1_byte=False,
        message_size=0
    )
