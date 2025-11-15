# -*- coding: utf-8 -*-

# OMRA by Starwear

# Импортируем библиотеки
import aiomysql, aiohttp

# Импортируем реализацию
from mrim.parsers import sms_parser
from mrim.proto_types import create_ul, build_header
from mrim.proto import MRIM_CS_SMS_ACK, MRIM_SMS_OK, MRIM_SMS_SERVICE_UNAVAILABLE
from utils import telegram_bot_token, logger

async def send_sms(writer, address, data, magic, proto, seq, connection, email):
    """Отправка SMS в Telegram"""
    # Парсим пакет
    parsed_data = await sms_parser(data, proto)

    # Создаем заголовок пакета
    header = await build_header(
        magic,
        proto,
        seq,
        MRIM_CS_SMS_ACK,
        4
    )

    # Ищем telegram id в бд
    async with connection.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("SELECT * FROM sms_info WHERE phone = %s", (parsed_data.get("phone"),))
        sms_data = await cursor.fetchone()

    # Если данные есть - продолжаем отправку
    if sms_data:
        # TG ID получателя
        telegram_id = sms_data.get("telegram_id")

        # Query параметры для запроса
        query = {
            "chat_id": telegram_id,
            "text": f"📬 Новое сообщение от {email}:\n{parsed_data.get('message')}"
        }

        # Высылаем сообщение в Telegram
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.telegram.org/bot{telegram_bot_token}/sendMessage', params=query) as response:
                response_send_msg = await response.json()

                # Если при отправке сообщения возникла ошибка - возвращаем ошибку клиенту
                if response_send_msg.get("ok") == False:
                    # Создаем пакет
                    response = header + await create_ul(MRIM_SMS_SERVICE_UNAVAILABLE)

                    # Отправляем
                    writer.write(response)
                    await writer.drain()
                    logger.info(f"Отправил команду MRIM_CS_SMS_ACK клиенту {address[0]}")

                    return

        # Создаем пакет
        response = header + await create_ul(MRIM_SMS_OK)

        # Отправляем
        writer.write(response)
        await writer.drain()
        logger.info(f"Отправил команду MRIM_CS_SMS_ACK клиенту {address[0]}")
    else:
        # Создаем пакет
        response = header + await create_ul(MRIM_SMS_SERVICE_UNAVAILABLE)

        # Отправляем
        writer.write(response)
        await writer.drain()
        logger.info(f"Отправил команду MRIM_CS_SMS_ACK клиенту {address[0]}")
