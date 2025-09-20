# -*- coding: utf-8 -*-

# OMRA by PostDevelopers

# Импортируем библиотеки
import asyncio, os, logging, ssl, hashlib, aiomysql, json
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
context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
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

                # Инициализируем SSL
                await writer.start_tls(context)

                # Формируем ответ
                response = await build_header(
                    unbuilded_header.get("magic"), # Магический заголовок
                    unbuilded_header.get("proto"), # Версия протокола
                    unbuilded_header.get("seq") + 1, # Очередь пакета
                    MRIM_CS_SSL_ACK, # Команда
                    0 # Размер пакета без заголовка
                )

                # Записываем ответ в сокет
                writer.write(response)
                await writer.drain()
                logger.info("Отправил команду MRIM_CS_SSL_ACK клиенту {}".format(address[0]))
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
                        "email": result_auth.get("email")
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
                await change_status(writer, connection, address, email, unbuilded_header.get("other_data"), unbuilded_header.get("proto"))
            else:
                logger.info("Неизвестная команда {}: {}".format(hex(unbuilded_header.get("command")), unbuilded_header))
    except Exception as error:
       logger.info("Произошла ошибка: {}".format(error))
    finally:
        # Закрываем подключение
        writer.close()
        await writer.wait_closed()
        connection.close()

        if email:
            del clients[address]
            del presences[address]

        logger.info("Словарь с клиентами: {}".format(clients))
        logger.info("Словарь с статусами: {}".format(presences))
        logger.info("Работа с клиентом {} завершена".format(address[0]))

async def login3(writer, data, magic, proto, seq, connection, address):
    """Обработка пакета MRIM_CS_LOGIN3"""
    # Парсим пакет
    parser_result = await login3_parser(data)

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

            # Выставляем никнейм контакта
            if result_account_data is None:
                contact_nickname = "[deleted]"
            else:
                contact_nickname = result_account_data.get("nickname")

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
                    xstatus_desc = presence.get("xstatus_desc")
                    status_num = presence.get("status")
                    com_support = presence.get("com_support")

            # Добавляем контакт в лист
            contacts_list += await create_ul(0) # flags
            contacts_list += await create_ul(contact.get("index")) # group id
            contacts_list += await create_lps(contact.get("email")) # email
            contacts_list += await create_lps(contact_nickname, "utf-16-le") # nickname
            contacts_list += await create_ul(contact.get("authorized")) # authorized
            contacts_list += await create_ul(status_num) # status
            contacts_list += await create_lps("") # phone
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

async def change_status(writer, connection, address, email, data, version):
    """Смена статуса пользователем"""
    async with connection.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("SELECT * FROM user_data WHERE email = %s", (email,))
        result_account_data = await cursor.fetchone()

    # Получаем контакты
    contacts = result_account_data.get("contacts")

    # Парсим пакет
    parsed_data = await change_status_parser(data, version)

    logger.info("Разобранный change_status: {}".format(parsed_data))

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