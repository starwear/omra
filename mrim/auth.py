# -*- coding: utf-8 -*-

# OMRA by Starwear

# Импортируем библиотеки
import hashlib, aiomysql, json

# Импортируем реализацию
from mrim.parsers import login2_parser, login3_parser
from mrim.proto_types import create_lps, create_ul, build_header
from mrim.proto import MRIM_CS_LOGIN_ACK, MRIM_CS_LOGIN_REJ, MRIM_CS_CONTACT_LIST2, MRIM_CS_USER_INFO, GET_CONTACTS_OK, CONTACT_FLAG_GROUP
from utils import presences, logger

async def login3(writer, data, magic, proto, seq, connection, address):
    """Обработка пакета MRIM_CS_LOGIN3"""
    # Парсим пакет
    parser_result = await login3_parser(data, proto)

    # Получаем данные
    email = parser_result.get("email")
    password = parser_result.get("password")
    version1 = parser_result.get("version1")
    version2 = parser_result.get("version2")

    # Проверка на наличие данных
    if not email or not password or not version1 or not version2:
        return {
            "result": "fail"
        }
  
    # Ищем аккаунт в базе данных
    async with connection.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        result_account = await cursor.fetchone()

    # Поиск данных аккаунта в базе данных
    async with connection.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("SELECT * FROM user_data WHERE email = %s", (email,))
        result_account_data = await cursor.fetchone()

    logger.info(f"Попытка входа с почтой {email}")

    # Проверка пароля
    if result_account is None or result_account_data is None:
        # Причина отклонения авторизации
        reason = await create_lps("Invalid login")

        # Собираем ответ
        response = await build_header(
            magic, # Магический заголовок
            proto, # Версия протокола
            seq + 1, # Очередь пакета
            MRIM_CS_LOGIN_REJ, # Команда
            len(reason) # Размер пакета без заголовка
        ) + reason

        # Записываем ответ в сокет
        writer.write(response)
        await writer.drain()
        logger.info(f"Отправил команду MRIM_CS_LOGIN_REJ клиенту {address[0]}")

        # Возвращаем результат авторизации
        return {
            "result": "fail"
        }

    # Получаем данные о аккаунте
    nickname = result_account_data.get("nickname")
    groups = result_account_data.get("groups")
    contacts = result_account_data.get("contacts")
    valid_password = result_account.get("password")

    # Проверка пароля
    if valid_password == password:
        # Собираем ответ
        response = await build_header(
            magic, # Магический заголовок
            proto, # Версия протокола
            seq + 1, # Очередь пакета
            MRIM_CS_LOGIN_ACK, # Команда
            0 # Размер пакета без заголовка
        )

        # Записываем ответ в сокет
        writer.write(response)
        await writer.drain()
        logger.info(f"Отправил команду MRIM_CS_LOGIN_ACK клиенту {address[0]}")

        # Отправляем данные о аккаунте
        await user_info(writer, nickname, address, magic, proto, seq)
        await contact_list(writer, groups, contacts, address, magic, proto, seq, connection, version2)

        # Возвращаем результат авторизации
        return {
            "result": "success",
            "email": email,
            "version1": version1,
            "version2": version2
        }
    else:
        # Причина отклонения авторизации
        reason = await create_lps("Invalid login")

        # Собираем ответ
        response = await build_header(
            magic, # Магический заголовок
            proto, # Версия протокола
            seq + 1, # Очередь пакета
            MRIM_CS_LOGIN_REJ, # Команда
            len(reason) # Размер пакета без заголовка
        ) + reason

        # Записываем ответ в сокет
        writer.write(response)
        await writer.drain()
        logger.info(f"Отправил команду MRIM_CS_LOGIN_REJ клиенту {address[0]}")

        # Возвращаем результат авторизации
        return {
            "result": "fail"
        }        

async def login2(writer, data, magic, proto, seq, connection, address):
    """Обработка пакета MRIM_CS_LOGIN2"""
    # Парсим пакет
    parser_result = await login2_parser(data, proto)

    # Получаем данные
    email = parser_result.get("email")
    password = parser_result.get("password")

    status = parser_result.get("status")
    xstatus_meaning = parser_result.get("xstatus_meaning")
    xstatus_title = parser_result.get("xstatus_title")
    xstatus_description = parser_result.get("xstatus_description")

    com_support = parser_result.get("com_support")

    version1 = parser_result.get("version1")
    version2 = parser_result.get("version2")

    language = parser_result.get("language")

    # Хешируем пароль в md5
    hashed_password = hashlib.md5(password.encode()).hexdigest()
  
    # Ищем аккаунт в базе данных
    async with connection.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        result_account = await cursor.fetchone()

    # Поиск данных аккаунта в базе данных
    async with connection.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("SELECT * FROM user_data WHERE email = %s", (email,))
        result_account_data = await cursor.fetchone()

    logger.info(f"Попытка входа с почтой {email}")

    # Проверка пароля
    if result_account is None or result_account_data is None:
        # Причина отклонения авторизации
        reason = await create_lps("Invalid login")

        # Собираем ответ
        response = await build_header(
            magic, # Магический заголовок
            proto, # Версия протокола
            seq + 1, # Очередь пакета
            MRIM_CS_LOGIN_REJ, # Команда
            len(reason) # Размер пакета без заголовка
        ) + reason

        # Записываем ответ в сокет
        writer.write(response)
        await writer.drain()
        logger.info(f"Отправил команду MRIM_CS_LOGIN_REJ клиенту {address[0]}")

        # Возвращаем результат авторизации
        return {
            "result": "fail"
        }

    # Получаем данные о аккаунте
    nickname = result_account_data.get("nickname")
    groups = result_account_data.get("groups")
    contacts = result_account_data.get("contacts")
    valid_password = result_account.get("password")

    # Проверка пароля
    if valid_password == hashed_password:
        # Собираем ответ
        response = await build_header(
            magic, # Магический заголовок
            proto, # Версия протокола
            seq + 1, # Очередь пакета
            MRIM_CS_LOGIN_ACK, # Команда
            0 # Размер пакета без заголовка
        )

        # Записываем ответ в сокет
        writer.write(response)
        await writer.drain()
        logger.info(f"Отправил команду MRIM_CS_LOGIN_ACK клиенту {address[0]}")

        # Отправляем данные о аккаунте
        await user_info(writer, nickname, address, magic, proto, seq)
        await contact_list(writer, groups, contacts, address, magic, proto, seq, connection, version2)

        # Возвращаем результат авторизации
        return {
            "result": "success",
            "email": email,
            "status": status,
            "xstatus_meaning": xstatus_meaning,
            "xstatus_title": xstatus_title,
            "xstatus_description": xstatus_description,
            "com_support": com_support,
            "version1": version1,
            "version2": version2
        }
    else:
        # Причина отклонения авторизации
        reason = await create_lps("Invalid login")

        # Собираем ответ
        response = await build_header(
            magic, # Магический заголовок
            proto, # Версия протокола
            seq + 1, # Очередь пакета
            MRIM_CS_LOGIN_REJ, # Команда
            len(reason) # Размер пакета без заголовка
        ) + reason

        # Записываем ответ в сокет
        writer.write(response)
        await writer.drain()
        logger.info(f"Отправил команду MRIM_CS_LOGIN_REJ клиенту {address[0]}")

        # Возвращаем результат авторизации
        return {
            "result": "fail"
        }        

async def user_info(writer, nickname, address, magic, proto, seq):
    """Отправка MRIM_CS_USER_INFO"""
    if proto in [65552, 65554, 65555, 65556, 65557, 65558, 65559]:
        msg_total = await create_lps("MESSAGES.TOTAL") + await create_lps("0", "utf-16-le")
        msg_unread = await create_lps("MESSAGES.UNREAD") + await create_lps("0", "utf-16-le")
        nickname = await create_lps("MRIM.NICKNAME") + await create_lps(nickname, "utf-16-le")
        endpoint = await create_lps("client.endpoint") + await create_lps(f"{address[0]}:{address[1]}", "utf-16-le")
    elif proto in [65543, 65544, 65545, 65546, 65547, 65548, 65549, 65550, 65551]:
        msg_total = await create_lps("MESSAGES.TOTAL") + await create_lps("0")
        msg_unread = await create_lps("MESSAGES.UNREAD") + await create_lps("0")
        nickname = await create_lps("MRIM.NICKNAME") + await create_lps(nickname)
        endpoint = await create_lps("client.endpoint") + await create_lps(f"{address[0]}:{address[1]}")

    result = msg_total + msg_unread + nickname + endpoint

    # Собираем ответ
    response = await build_header(
        magic, # Магический заголовок
        proto, # Версия протокола
        seq + 1, # Очередь пакета
        MRIM_CS_USER_INFO, # Команда
        len(result) # Размер пакета без заголовка
    ) + msg_total + msg_unread + nickname + endpoint

    # Записываем ответ в сокет
    writer.write(response)
    await writer.drain()
    logger.info(f"Отправил команду MRIM_CS_USER_INFO клиенту {address[0]}")

async def contact_list(writer, groups, contacts, address, magic, proto, seq, connection, user_agent):
    """Отправка MRIM_CS_CONTACT_LIST2"""
    # Загружаем группы и контакты в json
    groups = json.loads(groups)
    contacts = json.loads(contacts)

    # Формируем основу
    status = await create_ul(GET_CONTACTS_OK)
    groups_number = await create_ul(len(groups))
    groups_mask = await create_lps("us")
    contacts_mask = await create_lps("uussuussssusuuusssssu") # MRIM 1.23

    # Листы
    contact_list = b'' # Готовый лист с контактами
    group_list = b'' # Готовый лист с группами

    # Подбираем кодировку
    if proto in [65552, 65554, 65555, 65556, 65557, 65558, 65559]:
        # Костыль ебучий (как и сам мрим)
        if "QIP" in user_agent:
            encoding = "windows-1251"
        else:
            encoding = "utf-16-le"

        # Кодировка хстатусов
        xstatus_encoding = "utf-16-le"
    else:
        encoding = "windows-1251"
        xstatus_encoding = "windows-1251"

    group_index = 0

    # Добавляем группы в контакт-лист
    for group in groups:
        flags = CONTACT_FLAG_GROUP
        flags |= (group_index << 24)

        group_list += await create_ul(flags)
        group_list += await create_lps(group.get("name"), encoding)

        group_index += 1

    # Добавляем контактов в лист
    for contact in contacts:
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM user_data WHERE email = %s", (contact.get("email"),))
            result_account_data = await cursor.fetchone()

        # Получаем номер пользователя
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT phone FROM anketa WHERE email = %s", (contact.get("email"),))
            result_anketa_data = await cursor.fetchone()
        
        # Выставляем никнейм контакта
        if result_account_data is None:
            contact_nickname = "[deleted]"
        else:
            contact_nickname = result_account_data.get("nickname")

        # Извлечение номера телефона
        if result_account_data is None:
            phone = None
        else:
            phone = result_anketa_data.get("phone")

        # Если номера нет - выставляем пустую строку
        if phone is None:
            phone = ""

        # Статус
        xstatus_meaning = ""
        xstatus_title = ""
        xstatus_desc = ""
        status_num = 0
        com_support = 0

        # Ищем клиента в списке и записываем его статус
        for presence in presences.values():
            if presence.get("email") == contact.get("email"):
                # Сохраняем статус контакта
                xstatus_meaning = presence.get("xstatus_meaning")
                xstatus_title = presence.get("xstatus_title")
                xstatus_desc = presence.get("xstatus_description")
                status_num = presence.get("status")
                com_support = presence.get("com_support")

                # Фикс прикола с 5 агентами
                if proto in [65543, 65544, 65545, 65546, 65547, 65548, 65549] and status_num == 4:
                    status_num = 1

        # Извлечение кастомного никнейма
        custom_nickname = contact.get("custom_nickname")

        ### MRIM 1.7
        contacts_mask = await create_lps("uussuu")

        contact_list += await create_ul(contact.get("flags")) # flags
        contact_list += await create_ul(contact.get("index")) # group id
        contact_list += await create_lps(contact.get("email")) # email
        if custom_nickname:
            contact_list += await create_lps(custom_nickname, encoding) # nickname
        else:            
            contact_list += await create_lps(contact_nickname, encoding) # nickname
        contact_list += await create_ul(contact.get("authorized")) # authorized
        contact_list += await create_ul(status_num) # status

        ### MRIM 1.8, 1.9, 1.10, 1.11, 1.12, 1.13
        if proto > 65543:
            contacts_mask = await create_lps("uussuus")

            contact_list += await create_lps(phone) # phone

        ### MRIM 1.14, 1.15, 1.16, 1.18, 1.19
        if proto >= 65549:
            contacts_mask = await create_lps("uussuussssus")

            contact_list += await create_lps(xstatus_meaning) # xstatus meaning
            contact_list += await create_lps(xstatus_title, xstatus_encoding) # xstatus title
            contact_list += await create_lps(xstatus_desc, xstatus_encoding) # xstatus description
            contact_list += await create_ul(com_support) # com support
            contact_list += await create_lps("") # user agent 

        ### MRIM 1.20
        if proto >= 65556:
            contacts_mask = await create_lps("uussuussssusuuusss")

            contact_list += await create_ul(0) # ???
            contact_list += await create_ul(0) # ???
            contact_list += await create_ul(0) # ???
            contact_list += await create_lps("") # ???
            contact_list += await create_lps("") # ???
            contact_list += await create_lps("") # ???

        ### MRIM 1.21, 1.22
        if proto >= 65557:
            contacts_mask = await create_lps("uussuussssusuuussss")

            contact_list += await create_lps("") # ???

        ### MRIM 1.23
        if proto == 65559:
            contacts_mask = await create_lps("uussuussssusuuusssssu")

            contact_list += await create_lps("") # ???
            contact_list += await create_ul(0) # ???

    result = status + groups_number + groups_mask + contacts_mask + group_list + contact_list

    # Собираем ответ
    response = await build_header(
        magic, # Магический заголовок
        proto, # Версия протокола
        seq + 1, # Очередь пакета
        MRIM_CS_CONTACT_LIST2, # Команда
        len(result) # Размер пакета без заголовка
    ) + result

    # Записываем ответ в сокет
    writer.write(response)
    await writer.drain()
    logger.info(f"Отправил команду MRIM_CS_CONTACT_LIST2 клиенту {address[0]}")
