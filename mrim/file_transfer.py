# -*- coding: utf-8 -*-

# OMRA by Starwear

# Импортируем реализацию
from mrim.parsers import file_transfer_parser, file_transfer_ack_parser
from mrim.proto_types import create_lps, create_ul, build_header
from mrim.proto import MRIM_CS_FILE_TRANSFER, MRIM_CS_FILE_TRANSFER_ACK
from main import clients, logger

async def file_transfer(data, proto, email):
    """Передача файлов"""
    # Парсим данные пакета
    parsed_data = await file_transfer_parser(data, proto)

    # Ищем получателя в списке и отправляем ему пакет
    for client in clients.values():
        if client.get("email") == parsed_data.get("email"):
            # Извлекаем данные
            email = await create_lps(email)
            transfer_id = await create_ul(parsed_data.get("transfer_id"))
            total_size = await create_ul(parsed_data.get("total_size"))

            ### Сборка подстроки LPS
            file_desc = await create_lps(parsed_data.get("file_desc"))
            empty_param = await create_lps(parsed_data.get("empty_param"))
            connection_address = await create_lps(parsed_data.get("connection_address"))

            floor_lps = await create_lps(file_desc + empty_param + connection_address)

            # Собираем данные пакета
            result = email + transfer_id + total_size + floor_lps

            # Билдим пакет
            response = await build_header(
                client.get("magic"),
                client.get("proto"),
                1,
                MRIM_CS_FILE_TRANSFER,
                len(result)
            ) + result

            # Отправляем
            client.get("writer").write(response)
            await client.get("writer").drain()
            logger.info(f"Отправил команду MRIM_CS_FILE_TRANSFER клиенту {client.get('email')}")

async def file_transfer_ack(data, proto, email):
    """Отклонение / принятие передачи файлов"""
    # Парсим данные пакета
    parsed_data = await file_transfer_ack_parser(data, proto)

    # Ищем получателя в списке и отправляем ему пакет
    for client in clients.values():
        if client.get("email") == parsed_data.get("email"):
            # Извлекаем данные
            status = await create_ul(parsed_data.get("status"))
            email = await create_lps(email)
            transfer_id = await create_ul(parsed_data.get("transfer_id"))
            mirror_address = await create_lps(parsed_data.get('mirror_address'))

            # Собираем данные пакета
            result = status + email + transfer_id + mirror_address

            # Билдим пакет
            response = await build_header(
                client.get("magic"),
                client.get("proto"),
                1,
                MRIM_CS_FILE_TRANSFER_ACK,
                len(result)
            ) + result

            # Отправляем
            client.get("writer").write(response)
            await client.get("writer").drain()
            logger.info(f"Отправил команду MRIM_CS_FILE_TRANSFER_ACK клиенту {client.get('email')}")
