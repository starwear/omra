# -*- coding: utf-8 -*-

# OMRA by Starwear

# Импортируем secrets
import secrets

### Взаимодействие с протоколом

async def build_header(magic: int, proto: int, seq: int, command: int, size: int):
    """Сборка заголовка MRIM"""
    # Создаем заголовок
    magic = magic.to_bytes(4, "little") # Магический заголовок
    proto = proto.to_bytes(4, "little") # Версия протокола
    seq = seq.to_bytes(4, "little") # Очередь пакета
    command = command.to_bytes(4, "little") # Команда
    size = size.to_bytes(4, "little") # Размер пакета без заголовка
    fromip = bytearray(4) # Адрес отправителя
    fromport = bytearray(4) # Порт отправителя
    reserved = bytearray(16) # Зарезервировано

    # Собираем заголовок
    result = magic + proto + seq + command + size + fromip + fromport + reserved

    # Возращаем заголовок
    return result

async def unbuild_header(data: bytes):
    """Разборка заголовка MRIM"""
    # Разбираем заголовок
    magic = int.from_bytes(data[0:4], "little") # Магический заголовок
    proto = int.from_bytes(data[4:8], "little") # Версия протокола
    seq = int.from_bytes(data[8:12], "little") # Очередь пакета
    command = int.from_bytes(data[12:16], "little") # Команда
    size = int.from_bytes(data[16:20], "little") # Размер пакета без заголовка
    fromip = int.from_bytes(data[20:24], "little") # Адрес отправителя
    fromport = int.from_bytes(data[24:28], "little") # Порт отправителя
    reserved = int.from_bytes(data[28:44], "little") # Зарезервировано

    # Возращаем разобранный заголовок
    return {
        "magic": magic,
        "proto": proto,
        "seq": seq,
        "command": command,
        "size": size,
        "fromip": fromip,
        "fromport": fromport,
        "reserved": reserved
    }

async def create_ul(value: int):
    # Преобразуем число в байты
    result = value.to_bytes(4, "little")

    # Возвращаем результат
    return result

async def create_lps(value, encoding: str = "windows-1251"):
    # Кодируем строку в выбранную кодировку
    if type(value) == bytes:
        value_encoded = value
    else:
        value_encoded = value.encode(encoding)

    # Вычисляем длину строки
    value_length = await create_ul(len(value_encoded))

    # Результат
    result = value_length + value_encoded

    # Возвращаем
    return result

async def create_uidl():
    # Генерируем 8 символов
    result = secrets.token_urlsafe(6)

    # Возвращаем
    return result