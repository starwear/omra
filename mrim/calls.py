# -*- coding: utf-8 -*-

# OMRA by Starwear

# Импортируем реализацию
from mrim.proto_types import create_lps, create_ul, build_header
from mrim.proto import MRIM_CS_CALL, MRIM_CS_CALL_ACK
from mrim.parsers import call_parser, call_ack_parser
from utils import clients, logger

async def call(data, proto, email):
    """Звонки"""
    # Парсим данные пакета
    parsed_data = await call_parser(data, proto)

    # Ищем получателя в списке и отправляем ему пакет
    for client in clients.values():
        if client.get("email") == parsed_data.get("email"):
            # Собираем данные пакета
            email = await create_lps(email)
            transfer_id = await create_ul(parsed_data.get("transfer_id"))
            ips = await create_lps(parsed_data.get("ips"))

            result = email + transfer_id + ips

            # Билдим пакет
            response = await build_header(
                client.get("magic"),
                client.get("proto"),
                1,
                MRIM_CS_CALL,
                len(result)
            ) + result

            # Отправляем
            client.get("writer").write(response)
            await client.get("writer").drain()
            logger.info(f"Отправил команду MRIM_CS_CALL клиенту {client.get('email')}")

async def call_ack(data, proto, email):
    """Принятие / отклонение звонка"""
    # Парсим данные пакета
    parsed_data = await call_ack_parser(data, proto)

    # Ищем получателя в списке и отправляем ему пакет
    for client in clients.values():
        if client.get("email") == parsed_data.get("email"):
            # Собираем данные пакета
            call_status = await create_ul(parsed_data.get("call_status"))
            email = await create_lps(email)
            transfer_id = await create_ul(parsed_data.get("transfer_id"))

            result = call_status + email + transfer_id

            # Билдим пакет
            response = await build_header(
                client.get("magic"),
                client.get("proto"),
                1,
                MRIM_CS_CALL_ACK,
                len(result)
            ) + result

            # Отправляем
            client.get("writer").write(response)
            await client.get("writer").drain()
            logger.info(f"Отправил команду MRIM_CS_CALL_ACK клиенту {client.get('email')}")
