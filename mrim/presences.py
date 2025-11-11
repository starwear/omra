# -*- coding: utf-8 -*-

# OMRA by Starwear

# Импортируем библиотеки
import aiomysql, json

# Импортируем реализацию
from mrim.parsers import change_status_parser
from mrim.proto_types import *
from mrim.proto import MRIM_CS_USER_STATUS
from main import clients, presences, logger

async def change_status(connection, address, email, data, version):
    """Смена статуса пользователем"""
    # Получаем данные о аккаунте пользователя
    async with connection.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("SELECT * FROM user_data WHERE email = %s", (email,))
        result_account_data = await cursor.fetchone()

    # Получаем контакты
    contacts = result_account_data.get("contacts")

    # Парсим пакет
    parsed_data = await change_status_parser(data, version)

    # Заменяем статус в словаре
    presences[email]["status"] = parsed_data.get("status")
    presences[email]["xstatus_meaning"] = parsed_data.get("xstatus_meaning")
    presences[email]["xstatus_title"] = parsed_data.get("xstatus_title")
    presences[email]["xstatus_description"] = parsed_data.get("xstatus_description")
    presences[email]["com_support"] = parsed_data.get("com_support")

    # Сборка пакета
    status = await create_ul(parsed_data.get("status"))
    xstatus_meaning = await create_lps(parsed_data.get("xstatus_meaning"))
    xstatus_title_cp1251 = await create_lps(parsed_data.get("xstatus_title"))
    xstatus_description_cp1251 = await create_lps(parsed_data.get("xstatus_description"))
    xstatus_title_utf16 = await create_lps(parsed_data.get("xstatus_title"), "utf-16-le")
    xstatus_description_utf16 = await create_lps(parsed_data.get("xstatus_description"), "utf-16-le")
    email = await create_lps(email)
    com_support = await create_ul(parsed_data.get("com_support"))
    user_agent = await create_lps("")

    # Загружаем контакты в json
    contacts = json.loads(contacts)

    # Рассылка нового статуса всем контактам
    for contact in contacts:
        for client in clients.values():
            if client.get("email") == contact.get("email"):
                if client.get("proto") in [65543, 65544, 65545, 65546, 65547, 65548, 65549]:
                    packet_data = status + email

                    # Фикс прикола с 5 агентами
                    if parsed_data.get("status") == 4:
                        packet_data = await create_ul(1) + email
                elif client.get("proto") in [65550, 65551]:
                    packet_data = status + xstatus_meaning + xstatus_title_cp1251 + xstatus_description_cp1251 + email + com_support + user_agent
                elif client.get("proto") in [65552, 65554, 65555, 65556, 65557, 65558, 65559]:
                    packet_data = status + xstatus_meaning + xstatus_title_utf16 + xstatus_description_utf16 + email + com_support + user_agent
                else:
                    packet_data = status + email

                    # Фикс прикола с 5 агентами
                    if parsed_data.get("status") == 4:
                        packet_data = await create_ul(1) + email

                response = await build_header(
                    client.get("magic"),
                    client.get("proto"),
                    1,
                    MRIM_CS_USER_STATUS,
                    len(packet_data)
                ) + packet_data

                client.get("writer").write(response)
                await client.get("writer").drain()
                logger.info(f"Отправил пакет MRIM_CS_USER_STATUS пользователю {client.get('email')}")
