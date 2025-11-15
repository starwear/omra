# -*- coding: utf-8 -*-

# OMRA by Starwear

# Импортирование библиотек
import json, aiomysql, time

# Импортирование реализации
from utils import clients, logger, presences
from mrim.proto import MRIM_CS_USER_BLOG_STATUS
from mrim.parsers import microblog_change_parser
from mrim.proto_types import create_lps, create_ul, build_header

async def microblog_change(connection, email, data, version):
    """Добавление новой записи в микроблог"""
    # Получаем данные о аккаунте пользователя
    async with connection.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("SELECT * FROM user_data WHERE email = %s", (email,))
        result_account_data = await cursor.fetchone()

    # Получаем контакты
    contacts = json.loads( result_account_data.get("contacts") )

    # Парсим пакет
    parsed_data = await microblog_change_parser(data, version)

    id = 1
    note_time = int(time.time())
    text = parsed_data.get("message")
    reply = ""

    # Сборка пакета
    flags = await create_ul(parsed_data.get("flags"))
    user = await create_lps(email)
    idb = await create_ul(id)
    note_timeb = await create_ul(note_time)
    textb = await create_lps(text, "utf-16-le")
    replyb = await create_lps(reply)

    # Изменяем в словаре
    presences[email]["microblog"] = {
        "post_id": id,
        "time": note_time,
        "text": text,
        "reply_to": reply
    }

    # Рассылка записи всем контактам
    for contact in contacts:
        for client in clients.values():
            if client.get("email") == contact.get("email"):
                if client.get("proto") >= 65556:
                    # Данные пакета
                    packet_data = flags + user + idb + idb + note_timeb + textb + replyb

                    # Создание пакета
                    response = await build_header(
                        client.get("magic"),
                        client.get("proto"),
                        1,
                        MRIM_CS_USER_BLOG_STATUS,
                        len(packet_data)
                    ) + packet_data

                    # Отправляем пакет
                    client.get("writer").write(response)
                    await client.get("writer").drain()
                    logger.info(f"Отправил пакет MRIM_CS_USER_BLOG_STATUS пользователю {client.get('email')}")
