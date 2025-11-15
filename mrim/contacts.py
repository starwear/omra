# -*- coding: utf-8 -*-

# OMRA by Starwear

# Импортируем библиотеки
import aiomysql, json

# Импортируем реализацию
from mrim.parsers import add_contact_parser
from mrim.proto_types import create_ul, build_header
from mrim.proto import MRIM_CS_ADD_CONTACT_ACK, CONTACT_OPER_USER_EXISTS, CONTACT_OPER_SUCCESS, CONTACT_OPER_NO_SUCH_USER, CONTACT_FLAG_GROUP, CONTACT_OPER_GROUP_LIMIT
from utils import logger

async def add_contact(writer, connection, address, data, magic, proto, seq, email):
    async with connection.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("SELECT * FROM user_data WHERE email = %s", (email,))
        result_account_data = await cursor.fetchone()

    # Извлекаем список контактов
    contacts = json.loads(result_account_data.get("contacts"))

    # Извлекаем список групп
    groups = json.loads(result_account_data.get("groups"))

    # Парсим пакет
    parsed_data = await add_contact_parser(data, proto)

    if parsed_data.get("flags") == 0:
        """Добавление контакта"""
        # Ищем аккаунт пользователя, которого требуется добавить
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM user_data WHERE email = %s", (parsed_data.get("contact"),))
            result_account_data = await cursor.fetchone()

        # Если аккаунт существует
        if result_account_data:
            # Проверка на наличие этого пользователя в контакт-листе
            for contact in contacts:
                if contact.get("email") == parsed_data.get("contact"):
                    # Собираем пакет
                    status = await create_ul(CONTACT_OPER_USER_EXISTS)
                    contact_id = await create_ul(0xffffffff)
                    result = status + contact_id
                    size = len(result)

                    # Формируем пакет
                    response = await build_header(
                        magic,
                        proto,
                        seq,
                        MRIM_CS_ADD_CONTACT_ACK,
                        size
                    ) + result

                    # Записываем результат в сокет
                    writer.write(response)
                    await writer.drain()
                    logger.info(f"Отправил команду MRIM_CS_ADD_CONTACT_ACK клиенту {address[0]}")
                    return

            # Добавляем в список
            contacts.append(
                {
                    "flags": parsed_data.get("flags"),
                    "index": parsed_data.get("group_id"),
                    "email": parsed_data.get("contact"),
                    "authorized": 1,
                    "custom_nickname": parsed_data.get("name")
                }
            )

            # Обновляем список
            async with connection.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("UPDATE user_data SET contacts = %s WHERE email = %s", (json.dumps(contacts), email,))
            
            # Формируем данные пакета
            status = await create_ul(CONTACT_OPER_SUCCESS)
            contact_id = await create_ul(parsed_data.get("group_id"))
            result = status + contact_id
            size = len(result)

            # Формируем пакет
            response = await build_header(
                magic,
                proto,
                seq,
                MRIM_CS_ADD_CONTACT_ACK,
                size
            ) + result

            # Записываем результат в сокет
            writer.write(response)
            await writer.drain()
            logger.info(f"Отправил команду MRIM_CS_ADD_CONTACT_ACK клиенту {address[0]}")
        else:
            status = await create_ul(CONTACT_OPER_NO_SUCH_USER)
            contact_id = await create_ul(0xffffffff)
            result = status + contact_id
            size = len(result)

            # Формируем пакет
            response = await build_header(
                magic,
                proto,
                seq,
                MRIM_CS_ADD_CONTACT_ACK,
                size
            ) + result

            # Записываем результат в сокет
            writer.write(response)
            await writer.drain()
            logger.info(f"Отправил команду MRIM_CS_ADD_CONTACT_ACK клиенту {address[0]}")      
    elif parsed_data.get("flags") & CONTACT_FLAG_GROUP:
        """Создание группы"""
        # Добавляем группу в список
        if proto in [65543, 65544, 65545, 65546, 65547, 65548, 65549, 65550, 65551]:
            groups.append(
                {
                    "flags": 0,
                    "name": parsed_data.get("contact")
                }
            )
        else:
            groups.append(
                {
                    "flags": 0,
                    "name": parsed_data.get("name")
                }
            )

        # Проверка на количество групп
        if len(groups) > 20:
            status = await create_ul(CONTACT_OPER_GROUP_LIMIT)
            contact_id = await create_ul(0xffffffff)
            result = status + contact_id
            size = len(result)

            # Формируем пакет
            response = await build_header(
                magic,
                proto,
                seq,
                MRIM_CS_ADD_CONTACT_ACK,
                size
            ) + result

            # Записываем результат в сокет
            writer.write(response)
            await writer.drain()
            logger.info(f"Отправил команду MRIM_CS_ADD_CONTACT_ACK клиенту {address[0]}")      
            return

        # Обновляем список
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("UPDATE user_data SET `groups` = %s WHERE email = %s", (json.dumps(groups), email,))
            
        # Формируем данные пакета
        status = await create_ul(CONTACT_OPER_SUCCESS)
        contact_id = await create_ul(len(groups))
        result = status + contact_id
        size = len(result)

        # Формируем пакет
        response = await build_header(
            magic,
            proto,
            seq,
            MRIM_CS_ADD_CONTACT_ACK,
            size
        ) + result

        # Записываем результат в сокет
        writer.write(response)
        await writer.drain()
        logger.info("Отправил команду MRIM_CS_ADD_CONTACT_ACK клиенту {address[0]}")
