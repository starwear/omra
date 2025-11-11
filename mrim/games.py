# -*- coding: utf-8 -*-

# OMRA by Starwear

# Импортируем реализацию
from mrim.parsers import games_parser
from mrim.proto_types import create_lps, create_ul, build_header
from mrim.proto import MRIM_CS_GAME
from main import clients, logger

async def games(data, proto, email):
    """Игры"""
    # Парсим данные пакета
    parsed_data = await games_parser(data, proto)

    # Ищем получателя в списке и отправляем ему пакет
    for client in clients.values():
        if client.get("email") == parsed_data.get("email"):
            # Собираем данные пакета
            email = await create_lps(email)
            session_id = await create_ul(parsed_data.get("session_id"))
            game_msg = await create_ul(parsed_data.get("game_msg"))
            msg_id = await create_ul(parsed_data.get("msg_id"))
            time_send = await create_ul(parsed_data.get("time_send"))
            game_data = parsed_data.get("game_data")

            result = email + session_id + game_msg + msg_id + time_send + game_data

            # Билдим пакет
            response = await build_header(
                client.get("magic"),
                client.get("proto"),
                1,
                MRIM_CS_GAME,
                len(result)
            ) + result

            # Отправляем
            client.get("writer").write(response)
            await client.get("writer").drain()
            logger.info(f"Отправил команду MRIM_CS_GAME клиенту {client.get('email')}")
