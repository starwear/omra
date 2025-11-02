# -*- coding: utf-8 -*-

# OMRA by Starwear

# Импортируем библиотеки
import asyncio, os, logging, hashlib, aiomysql, json, time, aiohttp, ssl, base64
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

telegram_bot_token = os.environ.get("telegram_bot_token")

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
    greeted = False # Приветствовал ли клиент сервер
    authorized = False # Авторизация
    legacy_version = None # user-agent старого формата

    logger.info("Работаю с клиентом: {}".format(address[0]))

    # Подключение к базе данных
    connection = await aiomysql.connect(
        host=mysql_host,
        port=mysql_port,
        user=mysql_user,
        password=mysql_pass,
        db=mysql_base,
        autocommit=True
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
            payload = data[44:]

            # Обработка команд
            if unbuilded_header.get("command") == MRIM_CS_HELLO:
                # Приветствие клиента
                logger.info("Получил команду MRIM_CS_HELLO от клиента {}".format(address[0]))
                
                # Проверка приветствия
                if greeted == True:
                    break

                # Собираем ответ
                response = await build_header(
                    unbuilded_header.get("magic"), # Магический заголовок
                    unbuilded_header.get("proto"), # Версия протокола
                    unbuilded_header.get("seq") + 1, # Очередь пакета
                    MRIM_CS_HELLO_ACK, # Команда
                    4 # Размер пакета без заголовка
                ) + await create_ul(30) # keep-alive

                # Отмечаем в переменной приветствие
                greeted = True

                # Записываем ответ в сокет
                writer.write(response)
                await writer.drain()
                logger.info("Отправил команду MRIM_CS_HELLO_ACK клиенту {}".format(address[0]))
            elif unbuilded_header.get("command") == MRIM_CS_SSL:
                # Рукопожатие SSL
                logger.info("Получил команду MRIM_CS_SSL от клиента {}".format(address[0]))
                
                # Проверка приветствия
                if greeted == False:
                    break

                # Собираем ответ
                response = await build_header(
                    unbuilded_header.get("magic"), # Магический заголовок
                    unbuilded_header.get("proto"), # Версия протокола
                    unbuilded_header.get("seq"), # Очередь пакета
                    MRIM_CS_SSL_ACK, # Команда
                    0 # Размер пакета без заголовка
                )

                # Создание контекста SSL
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                context.load_cert_chain(certfile=os.environ.get("certfile_path"), keyfile=os.environ.get("keyfile_path"))

                # Записываем ответ в сокет
                writer.write(response)
                await writer.drain()
                logger.info("Отправил команду MRIM_CS_SSL_ACK клиенту {}".format(address[0]))

                # Начинаем пиздец и ужас
                await writer.start_tls(context)
            elif unbuilded_header.get("command") == MRIM_CS_LOGIN2:
                # Обработка MRIM_CS_LOGIN2
                logger.info("Получил команду MRIM_CS_LOGIN2 от клиента {}".format(address[0]))

                # Проверка приветствия и авторизации
                if greeted == False or authorized == True:
                    break

                # Выполняем авторизацию
                result_auth = await login2(writer, payload, unbuilded_header.get("magic"), unbuilded_header.get("proto"), unbuilded_header.get("seq"), connection, address)

                # Проверяем результат
                if result_auth.get("result") == "success":
                    email = result_auth.get("email")
                    presence_setted = False # Установлен ли статус клиента в словаре
                    authorized = True # Отмечаем в переменной авторизацию
                    legacy_version = result_auth.get("version2")

                    # Добавляем клиента в словарь
                    clients[address] = {
                        "writer": writer,
                        "legacy_version": result_auth.get("version2"),
                        "email": result_auth.get("email"),
                        "magic": unbuilded_header.get("magic"),
                        "proto": unbuilded_header.get("proto")
                    }

                    # Задаем статус в словаре
                    for presence in presences.values():
                        if presence.get("email") == email:
                            presences[email]["status"] = result_auth.get("status")
                            presences[email]["xstatus_meaning"] = result_auth.get("xstatus_meaning")
                            presences[email]["xstatus_title"] = result_auth.get("xstatus_title")
                            presences[email]["xstatus_description"] = result_auth.get("xstatus_description")
                            presence_setted = True

                    if presence_setted == False:
                        presences[email] = {
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
                    xstatus_meaning = await create_lps(result_auth.get("xstatus_meaning"))
                    xstatus_title_cp1251 = await create_lps(result_auth.get("xstatus_title"))
                    xstatus_description_cp1251 = await create_lps(result_auth.get("xstatus_description"))
                    xstatus_title_utf16 = await create_lps(result_auth.get("xstatus_title"), "utf-16-le")
                    xstatus_description_utf16 = await create_lps(result_auth.get("xstatus_description"), "utf-16-le")
                    email_encoded = await create_lps(email)
                    com_support = await create_ul(result_auth.get("com_support"))
                    user_agent = await create_lps("")

                    # Рассылка нового статуса всем контактам
                    for contact in contacts:
                        for client in clients.values():
                            if client.get("email") == contact.get("email"):
                                if client.get("proto") in [65543, 65544, 65545, 65546, 65547, 65548, 65549]:
                                    packet_data = status + email_encoded

                                    # Фикс прикола с 5 агентами
                                    if result_auth.get("status") == 4:
                                        packet_data = await create_ul(1) + email_encoded
                                elif client.get("proto") in [65550, 65551]:
                                    packet_data = status + xstatus_meaning + xstatus_title_cp1251 + xstatus_description_cp1251 + email_encoded + com_support + user_agent        
                                elif client.get("proto") in [65552, 65554, 65555, 65556, 65557, 65558, 65559]:
                                    packet_data = status + xstatus_meaning + xstatus_title_utf16 + xstatus_description_utf16 + email_encoded + com_support + user_agent
                                else:
                                    packet_data = status + email_encoded

                                    # Фикс прикола с 5 агентами
                                    if result_auth.get("status") == 4:
                                        packet_data = await create_ul(1) + email_encoded

                                response = await build_header(
                                    client.get("magic"),
                                    client.get("proto"),
                                    1,
                                    MRIM_CS_USER_STATUS,
                                    len(packet_data)
                                ) + packet_data

                                client.get("writer").write(response)
                                await client.get("writer").drain()
                                logger.info(f"Отправил пакет MRIM_CS_USER_STATUS пользователю {client.get("email")}")      
                else:
                    break
            elif unbuilded_header.get("command") == MRIM_CS_LOGIN3:
                # Обработка MRIM_CS_LOGIN3
                logger.info("Получил команду MRIM_CS_LOGIN3 от клиента {}".format(address[0]))

                # Проверка приветствия и авторизации
                if greeted == False or authorized == True:
                    break

                # Выполняем авторизацию
                result_auth = await login3(writer, payload, unbuilded_header.get("magic"), unbuilded_header.get("proto"), unbuilded_header.get("seq"), connection, address)

                # Проверяем результат
                if result_auth.get("result") == "success":
                    email = result_auth.get("email")
                    presence_setted = False # Установлен ли статус клиента в словаре
                    authorized = True # Отмечаем в переменной авторизацию
                    legacy_version = result_auth.get("version2")

                    # Добавляем клиента в словарь
                    clients[address] = {
                        "writer": writer,
                        "email": result_auth.get("email"),
                        "legacy_version": result_auth.get("version2"),
                        "magic": unbuilded_header.get("magic"),
                        "proto": unbuilded_header.get("proto")
                    }

                    # Задаем статус клиенту в словаре
                    for presence in presences.values():
                        if presence.get("email") == email:
                            presences[email]["status"] = 1
                            presences[email]["xstatus_meaning"] = "STATUS_ONLINE"
                            presences[email]["xstatus_title"] = "Онлайн"
                            presences[email]["xstatus_description"] = ""
                            presence_setted = True

                    if presence_setted == False:
                        presences[email] = {
                            "email": email,
                            "status": 1,
                            "xstatus_meaning": "STATUS_ONLINE",
                            "xstatus_title": "Онлайн",
                            "xstatus_description": "",
                            "com_support": 0x3FF
                        }

                    # Получаем данные о аккаунте пользователя
                    async with connection.cursor(aiomysql.DictCursor) as cursor:
                        await cursor.execute("SELECT * FROM user_data WHERE email = %s", (email,))
                        result_account_data = await cursor.fetchone()

                    # Получаем контакты
                    contacts = json.loads(result_account_data.get("contacts"))

                    # Собираем пакет
                    status = await create_ul(1)
                    xstatus_meaning = await create_lps("STATUS_ONLINE")
                    xstatus_title_cp1251 = await create_lps("Онлайн")
                    xstatus_description_cp1251 = await create_lps("")
                    xstatus_title_utf16 = await create_lps("Онлайн", "utf-16-le")
                    xstatus_description_utf16 = await create_lps("", "utf-16-le")
                    email_encoded = await create_lps(email)
                    com_support = await create_ul(0x3FF)
                    user_agent = await create_lps("")

                    # Рассылка нового статуса всем контактам
                    for contact in contacts:
                        for client in clients.values():
                            if client.get("email") == contact.get("email"):
                                if client.get("proto") in [65543, 65544, 65545, 65546, 65547, 65548, 65549]:
                                    packet_data = status + email_encoded

                                    # Фикс прикола с 5 агентами
                                    if result_auth.get("status") == 4:
                                        packet_data = await create_ul(1) + email_encoded
                                elif client.get("proto") in [65550, 65551]:
                                    packet_data = status + xstatus_meaning + xstatus_title_cp1251 + xstatus_description_cp1251 + email_encoded + com_support + user_agent       
                                elif client.get("proto") in [65552, 65554, 65555, 65556, 65557, 65558, 65559]:
                                    packet_data = status + xstatus_meaning + xstatus_title_utf16 + xstatus_description_utf16 + email_encoded + com_support + user_agent
                                else:
                                    packet_data = status + email_encoded

                                    # Фикс прикола с 5 агентами
                                    if result_auth.get("status") == 4:
                                        packet_data = await create_ul(1) + email_encoded

                                response = await build_header(
                                    client.get("magic"),
                                    client.get("proto"),
                                    1,
                                    MRIM_CS_USER_STATUS,
                                    len(packet_data)
                                ) + packet_data

                                client.get("writer").write(response)
                                await client.get("writer").drain()
                                logger.info(f"Отправил пакет MRIM_CS_USER_STATUS пользователю {client.get("email")}")    
                else:
                    break
            elif unbuilded_header.get("command") == 0x1090:
                # Хуй знает что это =(

                # Проверка приветствия
                if greeted == False:
                    break

                if authorized == False:
                    logger.info("Получил команду (maybe) MRIM_CS_LOGIN4 от клиента {}".format(address[0]))

                    # Выполняем авторизацию
                    result_auth = await login3(writer, payload[unbuilded_header.get("size") + 44:], unbuilded_header.get("magic"), unbuilded_header.get("proto"), unbuilded_header.get("seq"), connection, address)

                    # Проверяем результат
                    if result_auth.get("result") == "success":
                        email = result_auth.get("email")
                        presence_setted = False # Установлен ли статус клиента в словаре
                        authorized = True # Отмечаем в переменной авторизацию
                        legacy_version = result_auth.get("version2")

                        # Добавляем клиента в словарь
                        clients[address] = {
                            "writer": writer,
                            "email": result_auth.get("email"),
                            "legacy_version": result_auth.get("version2"),
                            "magic": unbuilded_header.get("magic"),
                            "proto": unbuilded_header.get("proto")
                        }

                        # Добавляем статус клиента в словарь
                        for presence in presences.values():
                            if presence.get("email") == email:
                                presences[email]["status"] = 1
                                presences[email]["xstatus_meaning"] = "STATUS_ONLINE"
                                presences[email]["xstatus_title"] = "Онлайн"
                                presences[email]["xstatus_description"] = ""
                                presence_setted = True

                        if presence_setted == False:
                            presences[email] = {
                                "email": email,
                                "status": 1,
                                "xstatus_meaning": "STATUS_ONLINE",
                                "xstatus_title": "Онлайн",
                                "xstatus_description": "",
                                "com_support": 0x3FF
                            }

                        # Получаем данные о аккаунте пользователя
                        async with connection.cursor(aiomysql.DictCursor) as cursor:
                            await cursor.execute("SELECT * FROM user_data WHERE email = %s", (email,))
                            result_account_data = await cursor.fetchone()

                        # Получаем контакты
                        contacts = json.loads(result_account_data.get("contacts"))

                        # Собираем пакет
                        status = await create_ul(1)
                        xstatus_meaning = await create_lps("STATUS_ONLINE")
                        xstatus_title_cp1251 = await create_lps("Онлайн")
                        xstatus_description_cp1251 = await create_lps("")
                        xstatus_title_utf16 = await create_lps("Онлайн", "utf-16-le")
                        xstatus_description_utf16 = await create_lps("", "utf-16-le")
                        email_encoded = await create_lps(email)
                        com_support = await create_ul(0x3FF)
                        user_agent = await create_lps("")

                        # Рассылка нового статуса всем контактам
                        for contact in contacts:
                            for client in clients.values():
                                if client.get("email") == contact.get("email"):
                                    if client.get("proto") in [65543, 65544, 65545, 65546, 65547, 65548, 65549]:
                                        packet_data = status + email_encoded

                                        # Фикс прикола с 5 агентами
                                        if result_auth.get("status") == 4:
                                            packet_data = await create_ul(1) + email_encoded
                                    elif client.get("proto") in [65550, 65551]:
                                        packet_data = status + xstatus_meaning + xstatus_title_cp1251 + xstatus_description_cp1251 + email_encoded + com_support + user_agent      
                                    elif client.get("proto") in [65552, 65554, 65555, 65556, 65557, 65558, 65559]:
                                        packet_data = status + xstatus_meaning + xstatus_title_utf16 + xstatus_description_utf16 + email_encoded + com_support + user_agent
                                    else:
                                        packet_data = status + email_encoded

                                        # Фикс прикола с 5 агентами
                                        if result_auth.get("status") == 4:
                                            packet_data = await create_ul(1) + email_encoded

                                    response = await build_header(
                                        client.get("magic"),
                                        client.get("proto"),
                                        1,
                                        MRIM_CS_USER_STATUS,
                                        len(packet_data)
                                    ) + packet_data

                                    client.get("writer").write(response)
                                    await client.get("writer").drain()
                                    logger.info(f"Отправил пакет MRIM_CS_USER_STATUS пользователю {client.get("email")}")    
                    else:
                        break
            elif unbuilded_header.get("command") == MRIM_CS_PING:
                # keep-alive
                logger.info("Получил команду MRIM_CS_PING от клиента {}".format(address[0]))

                # Проверка приветствия
                if greeted == False:
                    break
            elif unbuilded_header.get("command") == MRIM_CS_CHANGE_STATUS:
                # Смена статуса
                logger.info("Получил команду MRIM_CS_CHANGE_STATUS от клиента {}".format(address[0]))

                # Проверка приветствия и авторизации
                if greeted == False or authorized == False:
                    break

                await change_status(connection, address, email, payload, unbuilded_header.get("proto"))
            elif unbuilded_header.get("command") == MRIM_CS_WP_REQUEST:
                # Поиск
                logger.info("Получил команду MRIM_CS_WP_REQUEST от клиента {}".format(address[0]))

                # Проверка приветствия и авторизации
                if greeted == False or authorized == False:
                    break

                await wp_request(writer, connection, address, payload, unbuilded_header.get("magic"), unbuilded_header.get("proto"), unbuilded_header.get("seq"))
            elif unbuilded_header.get("command") == MRIM_CS_ADD_CONTACT:
                # Добавление контакта
                logger.info("Получил команду MRIM_CS_ADD_CONTACT от клиента {}".format(address[0]))

                # Проверка приветствия и авторизации
                if greeted == False or authorized == False:
                    break

                await add_contact(writer, connection, address, payload, unbuilded_header.get("magic"), unbuilded_header.get("proto"), unbuilded_header.get("seq"), email)
            elif unbuilded_header.get("command") == MRIM_CS_MODIFY_CONTACT:
                # Добавление контакта
                logger.info("Получил команду MRIM_CS_MODIFY_CONTACT от клиента {}".format(address[0]))

                # Проверка приветствия и авторизации
                if greeted == False or authorized == False:
                    break

                await modify_contact(writer, connection, address, payload, unbuilded_header.get("magic"), unbuilded_header.get("proto"), unbuilded_header.get("seq"), email)
            elif unbuilded_header.get("command") == MRIM_CS_MESSAGE:
                # Пакет сообщения
                logger.info("Получил команду MRIM_CS_MESSAGE от клиента {}".format(address[0]))

                # Проверка приветствия и авторизации
                if greeted == False or authorized == False:
                    break

                await new_message(writer, connection, address, payload, unbuilded_header.get("magic"), unbuilded_header.get("proto"), unbuilded_header.get("seq"), email, legacy_version)
            elif unbuilded_header.get("command") == MRIM_CS_MESSAGE_RECV:
                # Пакет о получении сообщения
                logger.info("Получил команду MRIM_CS_MESSAGE_RECV от клиента {}".format(address[0]))

                # Проверка приветствия и авторизации
                if greeted == False or authorized == False:
                    break

                await recv_message(payload, unbuilded_header.get("proto"))
            elif unbuilded_header.get("command") == MRIM_CS_AUTHORIZE:
                # Авторизация контакта
                logger.info("Получил команду MRIM_CS_AUTHORIZE от клиента {}".format(address[0]))

                # Проверка приветствия и авторизации
                if greeted == False or authorized == False:
                    break

                await authorize_contact(payload, connection, unbuilded_header.get("proto"), email)
            elif unbuilded_header.get("command") == MRIM_CS_GAME:
                # Игры
                logger.info("Получил команду MRIM_CS_GAME от клиента {}".format(address[0]))

                # Проверка приветствия и авторизации
                if greeted == False or authorized == False:
                    break

                await games(payload, unbuilded_header.get("proto"), email)
            elif unbuilded_header.get("command") == MRIM_CS_SMS:
                # Отправка SMS
                logger.info("Получил команду MRIM_CS_SMS от клиента {}".format(address[0]))

                # Проверка приветствия и авторизации
                if greeted == False or authorized == False:
                    break

                await send_sms(writer, address, payload, unbuilded_header.get("magic"), unbuilded_header.get("proto"), unbuilded_header.get("seq"), connection, email)
            elif unbuilded_header.get("command") == MRIM_CS_CALL:
                # Звонки
                logger.info("Получил команду MRIM_CS_CALL от клиента {}".format(address[0]))

                # Проверка приветствия и авторизации
                if greeted == False or authorized == False:
                    break

                await call(payload, unbuilded_header.get("proto"), email)
            elif unbuilded_header.get("command") == MRIM_CS_CALL_ACK:
                # Звонки
                logger.info("Получил команду MRIM_CS_CALL_ACK от клиента {}".format(address[0]))

                # Проверка приветствия и авторизации
                if greeted == False or authorized == False:
                    break

                await call_ack(payload, unbuilded_header.get("proto"), email)
            else:
                logger.info("Неизвестная команда {}: {}\n{}".format(hex(unbuilded_header.get("command")), unbuilded_header, payload))
    # except Exception as error:
    #    logger.info("Произошла ошибка: {}".format(error))
    finally:
        # Если пользователь авторизован, рассылаем всем контактам статус офлайн
        if email:
            # Удаляем пользователя из словаря
            try:
                del clients[address]
            except:
                pass

            count_sessions = 0

            for client in clients.values():
                if client.get("email") == email:
                    count_sessions += 1

            if count_sessions > 0:
                pass
            else:
                presences[email]["status"] = 0
                presences[email]["xstatus_meaning"] = ""
                presences[email]["xstatus_title"] = ""
                presences[email]["xstatus_description"] = ""

                # Получаем данные о аккаунте пользователя
                async with connection.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute("SELECT * FROM user_data WHERE email = %s", (email,))
                    result_account_data = await cursor.fetchone()

                # Получаем контакты
                contacts = json.loads(result_account_data.get("contacts"))

                # Собираем пакет
                status = await create_ul(0)
                xstatus_meaning = await create_lps("")
                xstatus_title = await create_lps("")
                xstatus_description = await create_lps("")
                email = await create_lps(email)
                com_support = await create_ul(0)
                user_agent = await create_lps("")

                # Рассылка нового статуса всем контактам
                for contact in contacts:
                    for client in clients.values():
                        if client.get("email") == contact.get("email"):
                            if client.get("proto") in [65543, 65544, 65545, 65546, 65547, 65548, 65549]:
                                packet_data = status + email
                                
                                response = await build_header(
                                    client.get("magic"),
                                    client.get("proto"),
                                    1,
                                    MRIM_CS_USER_STATUS,
                                    len(packet_data)
                                ) + packet_data

                                client.get("writer").write(response)
                                await client.get("writer").drain()
                                logger.info(f"Отправил пакет MRIM_CS_USER_STATUS пользователю {client.get("email")}")
                            elif client.get("proto") in [65550, 65551, 65552, 65554, 65555, 65556, 65557, 65558, 65559]:
                                packet_data = status + xstatus_meaning + xstatus_title + xstatus_description + email + com_support + user_agent
                                
                                response = await build_header(
                                    client.get("magic"),
                                    client.get("proto"),
                                    1,
                                    MRIM_CS_USER_STATUS,
                                    len(packet_data)
                                ) + packet_data

                                client.get("writer").write(response)
                                await client.get("writer").drain()
                                logger.info(f"Отправил пакет MRIM_CS_USER_STATUS пользователю {client.get("email")}")

        # Закрываем подключение
        writer.close()
        await writer.wait_closed()
        connection.close()

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
        logger.info("Отправил команду MRIM_CS_LOGIN_REJ клиенту {}".format(address[0]))

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
        endpoint = await create_lps("client.endpoint") + await create_lps("{}:{}".format(address[0], address[1]), "utf-16-le")
    elif proto in [65543, 65544, 65545, 65546, 65547, 65548, 65549, 65550, 65551]:
        msg_total = await create_lps("MESSAGES.TOTAL") + await create_lps("0")
        msg_unread = await create_lps("MESSAGES.UNREAD") + await create_lps("0")
        nickname = await create_lps("MRIM.NICKNAME") + await create_lps(nickname)
        endpoint = await create_lps("client.endpoint") + await create_lps("{}:{}".format(address[0], address[1]))

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
    logger.info("Отправил команду MRIM_CS_USER_INFO клиенту {}".format(address[0]))

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
    else:
        encoding = "windows-1251"

    # Добавляем группы в контакт-лист
    for group in groups:
        group_list += await create_ul(group.get("flags"))
        group_list += await create_lps(group.get("name"), encoding)

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
        if proto >= 65543:
            contacts_mask = await create_lps("uussuus")

            contact_list += await create_lps(phone) # phone

        ### MRIM 1.14, 1.15, 1.16, 1.18, 1.19
        if proto >= 65549:
            contacts_mask = await create_lps("uussuussssus")

            contact_list += await create_lps(xstatus_meaning, encoding) # xstatus meaning
            contact_list += await create_lps(xstatus_title, encoding) # xstatus title
            contact_list += await create_lps(xstatus_desc, encoding) # xstatus description
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

        # Собираем пакет
        response = await build_header(
            magic,
            proto,
            seq,
            MRIM_CS_ANKETA_INFO,
            len(result)
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

        # Выбор кодировки некоторых данных
        if proto in [65552, 65554, 65555, 65556, 65557, 65558, 65559]:
            encoding = "utf-16-le"
        else:
            encoding = "windows-1251"

        # Извлечение никнейма
        anketa_header_result += await create_lps("Nickname")
        if nickname:
            try:
                anketa_result += await create_lps(nickname, encoding)
            except:
                anketa_result += await create_lps(email, encoding)
        else:
            anketa_result += await create_lps(email, encoding)
        count_rows += 1

        # Извлечение домена
        anketa_header_result += await create_lps("Domain")
        anketa_result += await create_lps(domain)
        count_rows += 1

        # Добавление имени, если есть
        if firstname:
            anketa_header_result += await create_lps("FirstName")
            try:
                anketa_result += await create_lps(firstname, encoding)
            except:
                anketa_result += await create_lps("", encoding)
            count_rows += 1

        # Добавление фамилии, есть есть
        if lastname:
            anketa_header_result += await create_lps("LastName")
            try:
                anketa_result += await create_lps(lastname, encoding)
            except:
                anketa_result += await create_lps("", encoding)
            count_rows += 1

        # Добавление города, если есть
        if location:
            anketa_header_result += await create_lps("Location")
            try:
                anketa_result += await create_lps(location, encoding)
            except:
                anketa_result += await create_lps("", encoding)
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

        # Собираем пакет
        response = await build_header(
            magic,
            proto,
            seq,
            MRIM_CS_ANKETA_INFO,
            len(result)
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
                    logger.info("Отправил команду MRIM_CS_ADD_CONTACT_ACK клиенту {}".format(address[0]))
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
            logger.info("Отправил команду MRIM_CS_ADD_CONTACT_ACK клиенту {}".format(address[0]))
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
            logger.info("Отправил команду MRIM_CS_ADD_CONTACT_ACK клиенту {}".format(address[0]))      
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
            logger.info("Отправил команду MRIM_CS_ADD_CONTACT_ACK клиенту {}".format(address[0]))      
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
        logger.info("Отправил команду MRIM_CS_ADD_CONTACT_ACK клиенту {}".format(address[0]))

async def modify_contact(writer, connection, address, data, magic, proto, seq, email):
    """Изменение контакта (недопилено нихуя)"""
    async with connection.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("SELECT * FROM user_data WHERE email = %s", (email,))
        result_account_data = await cursor.fetchone()

    # Извлекаем список контактов
    contacts = json.loads(result_account_data.get("contacts"))

    # Извлекаем список групп
    groups = json.loads(result_account_data.get("groups"))

    # Парсим пакет
    parsed_data = await modify_contact_parser(data, proto)

    logger.info(parsed_data)

async def new_message(writer, connection, address, data, magic, proto, seq, email, legacy_version):
    """Отправка нового сообщения"""
    # Парсим пакет
    parsed_data = await new_message_parser(data, proto)

    # Собираем данные пакета MRIM_CS_MESSAGE_ACK
    msg_id = await create_ul(seq)
    flags = await create_ul(parsed_data.get("flags"))
    from_msg = await create_lps(email)
    message = await create_lps(parsed_data.get("message"))
    message_utf16 = await create_lps(parsed_data.get("message"), "utf-16-le")
    rtf_message = await create_lps(parsed_data.get("rtf_message"))

    # Отправлено ли сообщение
    message_sended = False

    # Ищем получателя в списке и отправляем ему сообщение
    for client in clients.values():
        if client.get("email") == parsed_data.get("to"):
            if client.get("proto") in [65552, 65554, 65555, 65556, 65557, 65558, 65559]:
                # Итоговые данные пакета
                if "QIP" in client.get("legacy_version"):
                    if parsed_data.get("flags") == 12:
                        if proto >= 65552:
                            # Декодим из base64
                            decoded_invite = base64.b64decode(parsed_data.get("message"))

                            # Парсим этот пиздец !!!
                            lps_count = decoded_invite[0:4]

                            nickname_length = int.from_bytes(decoded_invite[4:8], "little")
                            nickname_start = 8
                            nickname_end = nickname_start + nickname_length
                            nickname = await create_lps(decoded_invite[nickname_start:nickname_end].decode("utf-16-le"))

                            message_length = int.from_bytes(decoded_invite[nickname_end:nickname_end + 4], "little")
                            message_start = nickname_end + 4
                            message_end = message_start + message_length
                            message = await create_lps(decoded_invite[message_start:message_end].decode("utf-16-le").encode("windows-1251"))

                            # Пересобираем запрос авторизации
                            invite_recoded = lps_count + nickname + message

                            # Кодируем обратно в base64
                            message = await create_lps(base64.b64encode(invite_recoded))

                            result = msg_id + flags + from_msg + message + rtf_message

                            # Билдим пакет
                            response = await build_header(
                                client.get("magic"),
                                client.get("proto"), 
                                1,
                                MRIM_CS_MESSAGE_ACK,
                                len(result)
                            ) + result

                            # Отправляем
                            client.get("writer").write(response)
                            await client.get("writer").drain()
                            logger.info("Отправил команду MRIM_CS_MESSAGE_ACK клиенту {}".format(client.get("email")))

                            return

                    # Защита пирога с васьком от половины (а может быть и всех) пустых сообщений
                    if parsed_data.get("flags") & MESSAGE_FLAG_NOTIFY:
                        return

                    if "QIP" in client.get("legacy_version") and "QIP" in legacy_version:
                        result = msg_id + flags + from_msg + message_utf16 + rtf_message
                    else:
                        result = msg_id + flags + from_msg + message + rtf_message
                else:                    
                    result = msg_id + flags + from_msg + message_utf16 + rtf_message
            else:
                # Итоговые данные пакета
                result = msg_id + flags + from_msg + message + rtf_message

            # Билдим пакет
            response = await build_header(
                client.get("magic"),
                client.get("proto"), 
                1,
                MRIM_CS_MESSAGE_ACK,
                len(result)
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
            logger.info("Отправил команду MRIM_CS_AUTHORIZE_ACK клиенту {}".format(client.get("email")))

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
            logger.info("Отправил команду MRIM_CS_GAME клиенту {}".format(client.get("email")))

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
            "text": f"📬 Новое сообщение от {email}:\n{parsed_data.get("message")}"
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
                    logger.info("Отправил команду MRIM_CS_SMS_ACK клиенту {}".format(address[0]))

                    return

        # Создаем пакет
        response = header + await create_ul(MRIM_SMS_OK)

        # Отправляем
        writer.write(response)
        await writer.drain()
        logger.info("Отправил команду MRIM_CS_SMS_ACK клиенту {}".format(address[0]))
    else:
        # Создаем пакет
        response = header + await create_ul(MRIM_SMS_SERVICE_UNAVAILABLE)

        # Отправляем
        writer.write(response)
        await writer.drain()
        logger.info("Отправил команду MRIM_CS_SMS_ACK клиенту {}".format(address[0]))

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
            logger.info("Отправил команду MRIM_CS_CALL клиенту {}".format(client.get("email")))

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
            logger.info("Отправил команду MRIM_CS_CALL_ACK клиенту {}".format(client.get("email")))

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