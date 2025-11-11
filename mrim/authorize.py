# -*- coding: utf-8 -*-

# OMRA by Starwear

# Импортируем библиотеки
import aiomysql, json

# Импортируем реализацию
from mrim.parsers import authorize_parser
from mrim.proto_types import create_lps, build_header
from mrim.proto import MRIM_CS_AUTHORIZE_ACK
from main import clients, logger

async def authorize_contact(data, connection, proto, email):
    """Авторизация контакта"""
    # Парсим пакет
    parsed_data = await authorize_parser(data, proto)

    # Получаем информацию о аккаунте
    async with connection.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("SELECT * FROM user_data WHERE email = %s", (parsed_data.get("user"),))
        result_account_data = await cursor.fetchone()

    # Извлекаем контакты
    contacts = json.loads(result_account_data.get("contacts"))

    # Меняем статус авторизации
    for contact in contacts:
        if contact.get("email") == email:
            contact["authorized"] = 0

    # Обновляем в базе данных
    async with connection.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("UPDATE user_data SET contacts = %s WHERE email = %s", (json.dumps(contacts), parsed_data.get("user"),))

    # Ищем пользователя клиент которого хочет авторизовать
    for client in clients.values():
        if client.get("email") == parsed_data.get("user"):
            # Собираем данные пакета
            user = await create_lps(email)
            size = len(user)

            # Собираем пакет
            response = await build_header(
                client.get("magic"),
                client.get("proto"),
                1,
                MRIM_CS_AUTHORIZE_ACK,
                size
            ) + user

            # Отправляем
            client.get("writer").write(response)
            await client.get("writer").drain()
            logger.info(f"Отправил команду MRIM_CS_AUTHORIZE_ACK клиенту {client.get('email')}")
