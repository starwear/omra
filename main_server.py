# -*- coding: utf-8 -*-

# OMRA by Starwear

# Импортируем библиотеки
import asyncio, os, logging, ssl, hashlib, aiomysql, json, time
from dotenv import load_dotenv

# Импортируем реализацию
from mrim.proto_types import *
from mrim.proto import *
from mrim.parsers import *

# Загружаем конфигурацию
load_dotenv()

# Настройка логирования
logger = logging.getLogger("omra_main")
logging.basicConfig(level=logging.INFO)

# Настройка сервера
host = os.environ.get("main_host") # Хост
port = os.environ.get("main_port") # Порт

mysql_host = os.environ.get("mysql_host") # Хост mysql
mysql_port = int(os.environ.get("mysql_port")) # Порт mysql
mysql_user = os.environ.get("mysql_user")
mysql_pass = os.environ.get("mysql_pass")
mysql_base = os.environ.get("mysql_base")

# Создание контекста SSL
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.minimum_version = ssl.TLSVersion.SSLv3
context.load_cert_chain(certfile=os.environ.get("certfile_path"), keyfile=os.environ.get("keyfile_path"))

# Словарь клиентов
clients = {}

# Слоаврь статусов
presences = {}

async def handle_client(reader, writer):
    """Функция обработки подключений"""
    # Получение адреса подключения
    address = writer.get_extra_info("peername")

    # Настройки подключения
    email = None # Почта пользователя

    logger.info("Работаю с клиентом: {}".format(address[0]))

    # Подключение к базе данных
    connection = await aiomysql.connect(
        host=mysql_host,
        port=mysql_port,
        user=mysql_user,
        password=mysql_pass,
        db=mysql_base
    )

    try:
        while True:
            # Проверяем на наличие новых данных
            data = await reader.read(4096)

            # Если Клиент отключился
            if not data:
                break

            # Парсим заголовок
            unbuilded_header = await unbuild_header(data)

            # Обработка команд
            if unbuilded_header.get("command") == MRIM_CS_HELLO:
                # Приветствие клиента
                logger.info("Получил команду MRIM_CS_HELLO от клиента {}".format(address[0], address[1]))
                
                # Собираем ответ
                response = await build_header(
                    unbuilded_header.get("magic"), # Магический заголовок
                    unbuilded_header.get("proto"), # Версия протокола
                    unbuilded_header.get("seq") + 1, # Очередь пакета
                    MRIM_CS_HELLO_ACK, # Команда
                    4 # Размер пакета без заголовка
                ) + await create_ul(5) # keep-alive

                # Записываем ответ в сокет
                writer.write(response)
                await writer.drain()
                logger.info("Отправил команду MRIM_CS_HELLO_ACK клиенту {}".format(address[0]))
            elif unbuilded_header.get("command") == MRIM_CS_SSL:
                # Инициализация SSL
                logger.info("Получил команду MRIM_CS_SSL от клиента {}".format(address[0], address[1]))

                # Формируем ответ
                response = await build_header(
                    unbuilded_header.get("magic"), # Магический заголовок
                    unbuilded_header.get("proto"), # Версия протокола
                    unbuilded_header.get("seq") + 1, # Очередь пакета
                    MRIM_CS_SSL_ACK, # Команда
                    0 # Размер пакета без заголовка
                )

                # Инициализируем SSL
                try:
                    await writer.start_tls(context)
                except Exception as error:
                    logger.info(f"Ошибка SSL: {error}")
                    break 
                finally:
                    # Записываем ответ в сокет
                    writer.write(response)
                    await writer.drain()
                    logger.info("Отправил команду MRIM_CS_SSL_ACK клиенту {}".format(address[0]))
            elif unbuilded_header.get("command") == MRIM_CS_LOGIN2:
                # Обработка MRIM_CS_LOGIN2
                logger.info("Получил команду MRIM_CS_LOGIN2 от клиента {}".format(address[0], address[1]))
                logger.info("Разобранный заголовок: {}".format(unbuilded_header))

                # Выполняем авторизацию
                result_auth = await login2(writer, unbuilded_header.get("other_data"), unbuilded_header.get("magic"), unbuilded_header.get("proto"), unbuilded_header.get("seq"), connection, address)

                # Проверяем результат
                if result_auth.get("result") == "success":
                    email = result_auth.get("email")
                    presence_setted = False # Установлен ли статус клиента в словаре

                    clients[address] = {
                        "writer": writer,
                        "email": result_auth.get("email"),
                        "magic": unbuilded_header.get("magic"),
                        "proto": unbuilded_header.get("proto")
                    }

                    for presence in presences.values():
                        if presence.get("email") == email:
                            presences[email]["status"] = result_auth.get("status")
                            presences[email]["xstatus_meaning"] = result_auth.get("xstatus_meaning")
                            presences[email]["xstatus_title"] = result_auth.get("xstatus_title")
                            presences[email]["xstatus_description"] = result_auth.get("xstatus_description")
                            presence_setted = True

                    if presence_setted == False:
                        presences[address] = {
                            "email": email,
                            "status": result_auth.get("status"),
                            "xstatus_meaning": result_auth.get("xstatus_meaning"),
                            "xstatus_title": result_auth.get("xstatus_title"),
                            "xstatus_description": result_auth.get("xstatus_description"),
                            "com_support": result_auth.get("com_support")
                        }
                    
                    # Получаем данные о аккаунте пользователя
                    async with connection.cursor(aiomysql.DictCursor) as cursor:
                        await cursor.execute("SELECT * FROM user_data WHERE email = %s", (email,))
                        result_account_data = await cursor.fetchone()

                    # Получаем контакты
                    contacts = json.loads(result_account_data.get("contacts"))

                    # Собираем пакет
                    status = await create_ul(result_auth.get("status"))
                    email_in_lps = await create_lps(email)

                    response = status + email_in_lps

                    # Рассылка нового статуса всем контактам
                    for contact in contacts:
                        for client in clients.values():
                            if client.get("email") == contact.get("email"):
                                if client.get("proto") in [65543, 65544, 65545, 65546, 65547, 65548, 65549]:
                                    response = await build_header(
                                        client.get("magic"),
                                        client.get("proto"),
                                        1,
                                        MRIM_CS_USER_STATUS,
                                        len(response)
                                    ) + response

                                    client.get("writer").write(response)
                                    await client.get("writer").drain()
                                    logger.info(f"Отправил пакет MRIM_CS_USER_STATUS пользователю {client.get("email")}")

                    logger.info("Словарь с клиентами: {}".format(clients))
                    logger.info("Словарь с статусами: {}".format(presences))
                else:
                    break
            elif unbuilded_header.get("command") == MRIM_CS_LOGIN3:
                # Обработка MRIM_CS_LOGIN3
                logger.info("Получил команду MRIM_CS_LOGIN3 от клиента {}".format(address[0], address[1]))
                logger.info("Разобранный заголовок: {}".format(unbuilded_header))

                # Выполняем авторизацию
                result_auth = await login3(writer, unbuilded_header.get("other_data"), unbuilded_header.get("magic"), unbuilded_header.get("proto"), unbuilded_header.get("seq"), connection, address)

                # Проверяем результат
                if result_auth.get("result") == "success":
                    email = result_auth.get("email")
                    presence_setted = False # Установлен ли статус клиента в словаре

                    clients[address] = {
                        "writer": writer,
                        "email": result_auth.get("email"),
                        "magic": unbuilded_header.get("magic"),
                        "proto": unbuilded_header.get("proto")
                    }

                    for presence in presences.values():
                        if presence.get("email") == email:
                            presences[email]["status"] = 1
                            presences[email]["xstatus_meaning"] = "STATUS_ONLINE"
                            presences[email]["xstatus_title"] = "Онлайн"
                            presences[email]["xstatus_description"] = ""
                            presence_setted = True

                    if presence_setted == False:
                        presences[address] = {
                            "email": email,
                            "status": 1,
                            "xstatus_meaning": "STATUS_ONLINE",
                            "xstatus_title": "Онлайн",
                            "xstatus_description": "",
                            "com_support": 0x3FF
                        }
                    
                    logger.info("Словарь с клиентами: {}".format(clients))
                    logger.info("Словарь с статусами: {}".format(presences))
                else:
                    break
            elif unbuilded_header.get("command") == MRIM_CS_PING:
                logger.info("Получил команду MRIM_CS_PING от клиента {}".format(address[0], address[1]))
            elif unbuilded_header.get("command") == MRIM_CS_CHANGE_STATUS:
                logger.info("Получил команду MRIM_CS_CHANGE_STATUS от клиента {}".format(address[0]))
                await change_status(connection, address, email, unbuilded_header.get("other_data"), unbuilded_header.get("proto"))
            elif unbuilded_header.get("command") == MRIM_CS_WP_REQUEST:
                logger.info("Получил команду MRIM_CS_WP_REQUEST от клиента {}".format(address[0]))
                await wp_request(writer, connection, address, unbuilded_header.get("other_data"), unbuilded_header.get("magic"), unbuilded_header.get("proto"), unbuilded_header.get("seq"))
            elif unbuilded_header.get("command") == MRIM_CS_ADD_CONTACT:
                logger.info("Получил команду MRIM_CS_ADD_CONTACT от клиента {}".format(address[0]))
                await add_contact(writer, connection, address, unbuilded_header.get("other_data"), unbuilded_header.get("magic"), unbuilded_header.get("proto"), unbuilded_header.get("seq"), email)
            elif unbuilded_header.get("command") == MRIM_CS_MESSAGE:
                logger.info("Получил команду MRIM_CS_MESSAGE от клиента {}".format(address[0]))
                await new_message(writer, connection, address, unbuilded_header.get("other_data"), unbuilded_header.get("magic"), unbuilded_header.get("proto"), unbuilded_header.get("seq"), email)
            elif unbuilded_header.get("command") == MRIM_CS_MESSAGE_RECV:
                logger.info("Получил команду MRIM_CS_MESSAGE_RECV от клиента {}".format(address[0]))
                await recv_message(unbuilded_header.get("other_data"), unbuilded_header.get("proto"))
            elif unbuilded_header.get("command") == MRIM_CS_AUTHORIZE:
                logger.info("Получил команду MRIM_CS_AUTHORIZE от клиента {}".format(address[0]))
                await authorize_contact(unbuilded_header.get("other_data"), connection, unbuilded_header.get("proto"), email)
            else:
                logger.info("Неизвестная команда {}: {}".format(hex(unbuilded_header.get("command")), unbuilded_header))
    # except Exception as error:
    #    logger.info("Произошла ошибка: {}".format(error))
    finally:
        # Если пользователь авторизован, рассылаем всем контактам статус офлайн
        if email:
            # Удаляем пользователя из словарей
            del clients[address]
            del presences[address]

            # Получаем данные о аккаунте пользователя
            async with connection.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM user_data WHERE email = %s", (email,))
                result_account_data = await cursor.fetchone()

            # Получаем контакты
            contacts = json.loads(result_account_data.get("contacts"))

            # Собираем пакет
            status = await create_ul(0)
            email = await create_lps(email)

            response = status + email

            # Рассылка нового статуса всем контактам
            for contact in contacts:
                for client in clients.values():
                    if client.get("email") == contact.get("email"):
                        if client.get("proto") in [65543, 65544, 65545, 65546, 65547, 65548, 65549]:
                            response = await build_header(
                                client.get("magic"),
                                client.get("proto"),
                                1,
                                MRIM_CS_USER_STATUS,
                                len(response)
                            ) + response

                            client.get("writer").write(response)
                            await client.get("writer").drain()
                            logger.info(f"Отправил пакет MRIM_CS_USER_STATUS пользователю {client.get("email")}")

        # Закрываем подключение
        writer.close()
        await writer.wait_closed()
        connection.close()

        logger.info("Словарь с клиентами: {}".format(clients))
        logger.info("Словарь с статусами: {}".format(presences))
        logger.info("Работа с клиентом {} завершена".format(address[0]))

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

    # Проверка на наличие данных
    # if not email or not password or not version1 or not version2:
    #     return {
    #         "result": "fail"
    #     }
  
    # Ищем аккаунт в базе данных
    async with connection.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        result_account = await cursor.fetchone()

    # Поиск данных аккаунта в базе данных
    async with connection.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("SELECT * FROM user_data WHERE email = %s", (email,))
        result_account_data = await cursor.fetchone()

    logger.info("Попытка входа с почтой {}".format(email))

    # Проверка пароля
    if result_account is None or result_account_data is None:
        # Собираем ответ
        response = await build_header(
            magic, # Магический заголовок
            proto, # Версия протокола
            seq + 1, # Очередь пакета
            MRIM_CS_LOGIN_REJ, # Команда
            0 # Размер пакета без заголовка
        )

        # Записываем ответ в сокет
        writer.write(response)
        await writer.drain()
        logger.info("Отправил команду MRIM_CS_LOGIN_REJ клиенту {}".format(address[0]))

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
        logger.info("Отправил команду MRIM_CS_LOGIN_ACK клиенту {}".format(address[0]))

        # Отправляем данные о аккаунте
        await user_info(writer, nickname, address, magic, proto, seq)
        await contact_list(writer, groups, contacts, address, magic, proto, seq, connection)

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
        # Собираем ответ
        response = await build_header(
            magic, # Магический заголовок
            proto, # Версия протокола
            seq + 1, # Очередь пакета
            MRIM_CS_LOGIN_REJ, # Команда
            0 # Размер пакета без заголовка
        )

        # Записываем ответ в сокет
        writer.write(response)
        await writer.drain()
        logger.info("Отправил команду MRIM_CS_LOGIN_REJ клиенту {}".format(address[0]))

        # Возвращаем результат авторизации
        return {
            "result": "fail"
        }        

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

    logger.info("Попытка входа с почтой {}".format(email))

    # Проверка пароля
    if result_account is None or result_account_data is None:
        # Собираем ответ
        response = await build_header(
            magic, # Магический заголовок
            proto, # Версия протокола
            seq + 1, # Очередь пакета
            MRIM_CS_LOGIN_REJ, # Команда
            0 # Размер пакета без заголовка
        )

        # Записываем ответ в сокет
        writer.write(response)
        await writer.drain()
        logger.info("Отправил команду MRIM_CS_LOGIN_REJ клиенту {}".format(address[0]))

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
        logger.info("Отправил команду MRIM_CS_LOGIN_ACK клиенту {}".format(address[0]))

        # Отправляем данные о аккаунте
        await user_info(writer, nickname, address, magic, proto, seq)
        await contact_list(writer, groups, contacts, address, magic, proto, seq, connection)

        # Возвращаем результат авторизации
        return {
            "result": "success",
            "email": email
        }
    else:
        # Собираем ответ
        response = await build_header(
            magic, # Магический заголовок
            proto, # Версия протокола
            seq + 1, # Очередь пакета
            MRIM_CS_LOGIN_REJ, # Команда
            0 # Размер пакета без заголовка
        )

        # Записываем ответ в сокет
        writer.write(response)
        await writer.drain()
        logger.info("Отправил команду MRIM_CS_LOGIN_REJ клиенту {}".format(address[0]))

        # Возвращаем результат авторизации
        return {
            "result": "fail"
        }        

async def user_info(writer, nickname, address, magic, proto, seq):
    """Отправка MRIM_CS_USER_INFO"""
    if proto in [65559]:
        msg_total = await create_lps("MESSAGES.TOTAL") + await create_lps("0", "utf-16-le")
        msg_unread = await create_lps("MESSAGES.UNREAD") + await create_lps("0", "utf-16-le")
        nickname = await create_lps("MRIM.NICKNAME") + await create_lps(nickname, "utf-16-le")
        endpoint = await create_lps("client.endpoint") + await create_lps("{}:{}".format(address[0], address[1]), "utf-16-le")
    elif proto in [65543, 65544, 65545, 65546, 65547, 65548, 65549]:
        msg_total = await create_lps("MESSAGES.TOTAL") + await create_lps("0")
        msg_unread = await create_lps("MESSAGES.UNREAD") + await create_lps("0")
        nickname = await create_lps("MRIM.NICKNAME") + await create_lps(nickname)
        endpoint = await create_lps("client.endpoint") + await create_lps("{}:{}".format(address[0], address[1]))

    size = len(msg_total + msg_unread + nickname + endpoint)

    # Собираем ответ
    response = await build_header(
        magic, # Магический заголовок
        proto, # Версия протокола
        seq + 1, # Очередь пакета
        MRIM_CS_USER_INFO, # Команда
        size # Размер пакета без заголовка
    ) + msg_total + msg_unread + nickname + endpoint

    # Записываем ответ в сокет
    writer.write(response)
    await writer.drain()
    logger.info("Отправил команду MRIM_CS_USER_INFO клиенту {}".format(address[0]))

async def contact_list(writer, groups, contacts, address, magic, proto, seq, connection):
    """Отправка MRIM_CS_CONTACT_LIST2"""
    # Загружаем группы и контакты в json
    groups = json.loads(groups)
    contacts = json.loads(contacts)

    # Формируем основу
    status = await create_ul(GET_CONTACTS_OK)
    groups_number = await create_ul(len(groups))
    groups_mask = await create_lps("us")
    contacts_mask = await create_lps("uussuussssusuuusssssu")

    # Листы
    contacts_list = b'' # Готовый лист с контактами
    groups_list = b'' # Готовый лист с группами

    if proto in [65559]:
        # Добавляем группы в контакт-лист
        for group in groups:
            groups_list += await create_ul(0)
            groups_list += await create_lps(group.get("group_name"), "utf-16-le")

        # Добавляем контактов в контакт-лист
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
            phone = result_anketa_data.get("phone")

            if phone is None:
                phone = ""

            # Статус
            xstatus_meaning = ""
            xstatus_title = ""
            xstatus_desc = ""
            status_num = 0
            com_support = 0

            # Ищем клиента в списке и добавляем его статус
            for presence in presences.values():
                if presence.get("email") == contact.get("email"):
                    # Сохраняем статус контакта
                    xstatus_meaning = presence.get("xstatus_meaning")
                    xstatus_title = presence.get("xstatus_title")
                    xstatus_desc = presence.get("xstatus_description")
                    status_num = presence.get("status")
                    com_support = presence.get("com_support")

            # Извлечение кастомного никнейма
            custom_nickname = contact.get("custom_nickname")

            # Добавляем контакт в лист
            contacts_list += await create_ul(contact.get("flags")) # flags
            contacts_list += await create_ul(contact.get("index")) # group id
            contacts_list += await create_lps(contact.get("email")) # email
            if custom_nickname:
                contacts_list += await create_lps(custom_nickname, "utf-16-le") # nickname
            else:            
                contacts_list += await create_lps(contact_nickname, "utf-16-le") # nickname
            contacts_list += await create_ul(contact.get("authorized")) # authorized
            contacts_list += await create_ul(status_num) # status
            contacts_list += await create_lps(phone) # phone
            contacts_list += await create_lps(xstatus_meaning) # xstatus meaning
            contacts_list += await create_lps(xstatus_title, "utf-16-le") # xstatus title
            contacts_list += await create_lps(xstatus_desc, "utf-16-le") # xstatus description
            contacts_list += await create_ul(com_support) # com_support
            contacts_list += await create_lps("") # user agent
            contacts_list += await create_ul(0) # ???
            contacts_list += await create_ul(0) # ???
            contacts_list += await create_ul(0) # ???
            contacts_list += await create_lps("", "utf-16-le") # похоже микроблог
            contacts_list += await create_lps("", "utf-16-le") # ???
            contacts_list += await create_lps("", "utf-16-le") # ???
            contacts_list += await create_lps("", "utf-16-le") # ???
            contacts_list += await create_lps("", "utf-16-le") # ???
            contacts_list += await create_ul(0) # ???
    elif proto in [65544, 65545, 65546, 65547, 65548, 65549]:
        # Выставляем нужную маску
        contacts_mask = await create_lps("uussuus")

        # Добавляем группы в контакт-лист
        for group in groups:
            groups_list += await create_ul(0)
            groups_list += await create_lps(group.get("group_name"))

        # Добавляем контактов в контакт-лист
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
            phone = result_anketa_data.get("phone")

            if phone is None:
                phone = ""

            # Статус
            status_num = 0

            # Ищем клиента в списке и сохраняемм его статус
            for presence in presences.values():
                if presence.get("email") == contact.get("email"):
                    # Сохраняем статус контакта
                    status_num = presence.get("status")

            # Извлечение кастомного никнейма
            custom_nickname = contact.get("custom_nickname")

            # Добавляем контакт в лист
            contacts_list += await create_ul(contact.get("flags")) # flags
            contacts_list += await create_ul(contact.get("index")) # group id
            contacts_list += await create_lps(contact.get("email")) # email
            if custom_nickname:
                contacts_list += await create_lps(custom_nickname) # nickname
            else:
                contacts_list += await create_lps(contact_nickname) # nickname
            contacts_list += await create_ul(contact.get("authorized")) # authorized
            contacts_list += await create_ul(status_num) # status
            contacts_list += await create_lps(phone) # phone
    elif proto in [65543]:
        # Выставляем нужную маску
        contacts_mask = await create_lps("uussuu")

        # Добавляем группы в контакт-лист
        for group in groups:
            groups_list += await create_ul(0)
            groups_list += await create_lps(group.get("group_name"))

        # Добавляем контактов в контакт-лист
        for contact in contacts:
            async with connection.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM user_data WHERE email = %s", (contact.get("email"),))
                result_account_data = await cursor.fetchone()

            # Выставляем никнейм контакта
            if result_account_data is None:
                contact_nickname = "[deleted]"
            else:
                contact_nickname = result_account_data.get("nickname")

            # Статус
            status_num = 0

            # Ищем клиента в списке и сохраняемм его статус
            for presence in presences.values():
                if presence.get("email") == contact.get("email"):
                    # Сохраняем статус контакта
                    status_num = presence.get("status")

            # Извлечение кастомного никнейма
            custom_nickname = contact.get("custom_nickname")

            # Добавляем контакт в лист
            contacts_list += await create_ul(contact.get("flags")) # flags
            contacts_list += await create_ul(contact.get("index")) # group id
            contacts_list += await create_lps(contact.get("email")) # email
            if custom_nickname:
                contacts_list += await create_lps(custom_nickname) # nickname
            else:
                contacts_list += await create_lps(contact_nickname) # nickname
            contacts_list += await create_ul(contact.get("authorized")) # authorized
            contacts_list += await create_ul(status_num) # status  

    size = len(status + groups_number + groups_mask + contacts_mask + groups_list + contacts_list)

    # Собираем ответ
    response = await build_header(
        magic, # Магический заголовок
        proto, # Версия протокола
        seq + 1, # Очередь пакета
        MRIM_CS_CONTACT_LIST2, # Команда
        size # Размер пакета без заголовка
    ) + status + groups_number + groups_mask + contacts_mask + groups_list + contacts_list

    # Записываем ответ в сокет
    writer.write(response)
    await writer.drain()
    logger.info("Отправил команду MRIM_CS_CONTACT_LIST2 клиенту {}".format(address[0]))

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
    presences[address]["status"] = parsed_data.get("status")
    presences[address]["xstatus_meaning"] = parsed_data.get("xstatus_meaning")
    presences[address]["xstatus_title"] = parsed_data.get("xstatus_title")
    presences[address]["xstatus_description"] = parsed_data.get("xstatus_description")
    presences[address]["com_support"] = parsed_data.get("com_support")

    # Сборка пакета
    status = await create_ul(parsed_data.get("status"))
    email = await create_lps(email)

    response = status + email

    # Загружаем контакты в json
    contacts = json.loads(contacts)

    # Рассылка нового статуса всем контактам
    for contact in contacts:
        for client in clients.values():
            if client.get("email") == contact.get("email"):
                if client.get("proto") in [65543, 65544, 65545, 65546, 65547, 65548, 65549]:
                    response = await build_header(
                        client.get("magic"),
                        client.get("proto"),
                        1,
                        MRIM_CS_USER_STATUS,
                        len(response)
                    ) + response

                    client.get("writer").write(response)
                    await client.get("writer").drain()
                    logger.info(f"Отправил пакет MRIM_CS_USER_STATUS пользователю {client.get("email")}")

async def wp_request(writer, connection, address, data, magic, proto, seq):
    """Обработка MRIM_CS_WP_REQUEST (поиск)"""
    # Парсим данные
    parsed_data = await wp_request_parser(data, proto)

    email_parts = {}

    for value in parsed_data:
        if value.get("field") == MRIM_CS_WP_REQUEST_PARAM_USER:
            email_parts["login"] = value.get("value")
        elif value.get("field") == MRIM_CS_WP_REQUEST_PARAM_DOMAIN:
            email_parts["domain"] = value.get("value")
        else:
            return
    
    email = f"{email_parts.get("login")}@{email_parts.get("domain")}"

    # Получаем данные о аккаунте пользователя
    async with connection.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("SELECT * FROM user_data WHERE email = %s", (email,))
        result_account_data = await cursor.fetchone()

    # Получаем анкету пользователя
    async with connection.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("SELECT * FROM anketa WHERE email = %s", (email,))
        result_anketa_data = await cursor.fetchone()

    # Если пользователя не существует
    if result_account_data is None or result_anketa_data is None:
        # Формируем пакет
        status = await create_ul(MRIM_ANKETA_INFO_STATUS_NOUSER)
        count_rows = await create_ul(0)
        max_rows = await create_ul(10)
        current_time = await create_ul(int(time.time()))

        # Собираем данные пакета
        result = status + count_rows + max_rows + current_time

        # Размер пакета без заголовка
        size = len(result)

        # Собираем пакет
        response = await build_header(
            magic,
            proto,
            seq,
            MRIM_CS_ANKETA_INFO,
            size
        ) + result

        # Записываем ответ в сокет
        writer.write(response)
        await writer.drain()
        logger.info(f"Отправил команду MRIM_CS_ANKETA_INFO клиенту {address[0]}")
    else:
        # Итоговая анкета пользователя
        anketa_result = b''
        anketa_header_result = b''

        # Заголовок ответа
        status = MRIM_ANKETA_INFO_STATUS_OK
        count_rows = 0
        max_rows = 10
        current_time = int(time.time())

        ### Сборка анкеты

        # Извлечение данных о анкете
        username = result_anketa_data.get("username")
        nickname = result_account_data.get("nickname")
        domain = result_anketa_data.get("domain")
        firstname = result_anketa_data.get("firstname")
        lastname = result_anketa_data.get("lastname")
        location = result_anketa_data.get("location")
        birthday = result_anketa_data.get("birthday")
        zodiac = result_anketa_data.get("zodiac")
        phone = result_anketa_data.get("phone")
        sex = result_anketa_data.get("sex")

        # Извлечение юзернейма
        anketa_header_result += await create_lps("Username")
        anketa_result += await create_lps(username)
        count_rows += 1

        # Извлечение никнейма
        anketa_header_result += await create_lps("Nickname")
        if nickname:
            anketa_result += await create_lps(nickname)
        else:
            anketa_result += await create_lps(email)
        count_rows += 1

        # Извлечение домена
        anketa_header_result += await create_lps("Domain")
        anketa_result += await create_lps(domain)
        count_rows += 1

        # Добавление имени, если есть
        if firstname:
            anketa_header_result += await create_lps("FirstName")
            anketa_result += await create_lps(firstname)
            count_rows += 1

        # Добавление фамилии, есть есть
        if lastname:
            anketa_header_result += await create_lps("LastName")
            anketa_result += await create_lps(lastname)
            count_rows += 1

        # Добавление города, если есть
        if location:
            anketa_header_result += await create_lps("Location")
            anketa_result += await create_lps(location)
            count_rows += 1

        # Добавление дня рождения, если есть
        if birthday:
            anketa_header_result += await create_lps("Birthday")
            anketa_result += await create_lps(birthday)
            count_rows += 1
        
        # Добавление знака зодиака, если есть
        if zodiac:
            anketa_header_result += await create_lps("Zodiac")
            anketa_result += await create_lps(zodiac)
            count_rows += 1

        # Добавление номера телефона, если есть
        if phone:
            anketa_header_result += await create_lps("Phone")
            anketa_result += await create_lps(phone)
            count_rows += 1

        # Добавление пола, если есть
        if sex:
            anketa_header_result += await create_lps("Sex")
            anketa_result += await create_lps(sex)
            count_rows += 1

        status = await create_ul(status)
        count_rows = await create_ul(count_rows)
        max_rows = await create_ul(max_rows)
        current_time = await create_ul(current_time)

        ### Итоговые данные пакета
        result = status + count_rows + max_rows + current_time + anketa_header_result + anketa_result

        # Размер пакета без заголовка
        size = len(result)

        # Собираем пакет
        response = await build_header(
            magic,
            proto,
            seq,
            MRIM_CS_ANKETA_INFO,
            size
        ) + result

        writer.write(response)
        await writer.drain()
        logger.info(f"Отправил команду MRIM_CS_ANKETA_INFO клиенту {address[0]}")

async def add_contact(writer, connection, address, data, magic, proto, seq, email):
    async with connection.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("SELECT * FROM user_data WHERE email = %s", (email,))
        result_account_data = await cursor.fetchone()

    # Извлекаем список контактов
    contacts = json.loads(result_account_data.get("contacts"))

    # Парсим пакет
    parsed_data = await add_contact_parser(data, proto)

    logger.info(parsed_data)

    if parsed_data.get("flags") == 0:
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
                    contact_id = await create_ul(-1)
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
                    logger.info("Отправил команду MRIM_CS_ADD_CONTACT_ACK клиенту {}".format(address[0]))

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
            
            # Комитим изменения
            await connection.commit()

            # Формируем данные пакета
            status = await create_ul(CONTACT_OPER_SUCCESS)
            contact_id = await create_ul( parsed_data.get("group_id"))
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
            logger.info("Отправил команду MRIM_CS_ADD_CONTACT_ACK клиенту {}".format(address[0]))
        else:
            status = await create_ul(CONTACT_OPER_NO_SUCH_USER)
            contact_id = await create_ul(-1)
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
            logger.info("Отправил команду MRIM_CS_ADD_CONTACT_ACK клиенту {}".format(address[0]))      

async def new_message(writer, connection, address, data, magic, proto, seq, email):
    """Отправка нового сообщения"""
    # Парсим пакет
    parsed_data = await new_message_parser(data, proto)

    # Собираем данные пакета MRIM_CS_MESSAGE_ACK
    msg_id = await create_ul(seq)
    flags = await create_ul(parsed_data.get("flags"))
    from_msg = await create_lps(email)
    message = await create_lps(parsed_data.get("message"))
    rtf_message = await create_lps(parsed_data.get("rtf_message"))

    # Итоговые данные пакета
    result = msg_id + flags + from_msg + message + rtf_message
    size = len(result)

    # Отправлено ли сообщение
    message_sended = False

    # Ищем получателя в списке и отправляем ему сообщение
    for client in clients.values():
        if client.get("email") == parsed_data.get("to"):
            # Билдим пакет
            response = await build_header(
                client.get("magic"),
                client.get("proto"), 
                1,
                MRIM_CS_MESSAGE_ACK,
                size
            ) + result

            # Отправляем
            client.get("writer").write(response)
            await client.get("writer").drain()
            logger.info("Отправил команду MRIM_CS_MESSAGE_ACK клиенту {}".format(client.get("email")))
            message_sended = True
    
    if message_sended == False:
        # Билдим пакет
        response = await build_header(
            magic,
            proto, 
            seq,
            MRIM_CS_MESSAGE_STATUS,
            4
        ) + await create_ul(MESSAGE_REJECTED_DENY_OFFMSG)

        # Отправляем
        writer.write(response)
        await writer.drain()
        logger.info("Отправил команду MRIM_CS_MESSAGE_STATUS клиенту {}".format(address[0]))

async def recv_message(data, proto):
    """Обработка MRIM_CS_MESSAGE_RECV"""
    # Парсим данные пакета
    parsed_data = await recv_message_parser(data, proto)

    # Ищем получателя в списке и отправляем ему сообщение
    for client in clients.values():
        if client.get("email") == parsed_data.get("from"):
            # Билдим пакет
            response = await build_header(
                client.get("magic"),
                client.get("proto"),
                parsed_data.get("msg_id"),
                MRIM_CS_MESSAGE_STATUS,
                4
            ) + await create_ul(MESSAGE_DELIVERED)

            # Отправляем
            client.get("writer").write(response)
            await client.get("writer").drain()
            logger.info("Отправил команду MRIM_CS_MESSAGE_STATUS клиенту {}".format(client.get("email")))

async def authorize_contact(data, connection, proto, email):
    """Авторизация контакта"""
    # Парсим пакет
    parsed_data = await authorize_parser(data, proto)

    # Получаем информацию о аккаунте
    async with connection.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("SELECT * FROM user_data WHERE email = %s", (email,))
        result_account_data = await cursor.fetchone()

    # Извлекаем контакты
    contacts = json.loads(result_account_data.get("contacts"))

    # Меняем статус авторизации и отп
    for contact in contacts:
        if contact.get("email") == parsed_data.get("user"):
            contact["authorized"] = 0

    # Превращаем в json
    contacts = json.dumps(contacts)

    # Обновляем в базе данных
    async with connection.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("UPDATE user_data SET contacts = %s WHERE email = %s", (contacts, email,))
        await connection.commit()

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
            logger.info("Отправил команду MRIM_CS_AUTHORIZE_ACK клиенту {}".format(client.get("email")))
        

async def main():
    """Главная функция сервера"""
    server = await asyncio.start_server(handle_client, host, port)
    
    async with server:
        logger.info("Сервер запущен на порту {}".format(port))
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Произошла ошибка: KeyboardInterrupt")
    except Exception as error:
        logger.info("Произошла ошибка: {}".format(error))