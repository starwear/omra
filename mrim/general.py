# -*- coding: utf-8 -*-

# OMRA by Starwear

# Импортируем библиотеки
import asyncio, os, aiomysql, json, ssl
from dotenv import load_dotenv

# Импортируем реализацию
from mrim.proto_types import *
from mrim.proto import *
from mrim.parsers import *
from mrim.auth import *
from mrim.presences import *
from mrim.search import *
from mrim.contacts import *
from mrim.messages import *
from mrim.authorize import *
from mrim.calls import *
from mrim.file_transfer import *
from mrim.sms import *
from mrim.games import *

from utils import clients, presences, logger

# Загружаем конфигурацию
load_dotenv()

# Настройка сервера
host = os.environ.get("main_host") # Хост
port = os.environ.get("main_port") # Порт

mysql_host = os.environ.get("mysql_host") # Хост mysql
mysql_port = int(os.environ.get("mysql_port")) # Порт mysql
mysql_user = os.environ.get("mysql_user") # Юзер mysql
mysql_pass = os.environ.get("mysql_pass") # Пароль mysql
mysql_base = os.environ.get("mysql_base") # Имя базы

async def handle_client(reader, writer):
    """Функция обработки подключений"""
    # Получение адреса подключения
    address = writer.get_extra_info("peername")

    # Настройки подключения
    email = None # Почта пользователя
    greeted = False # Приветствовал ли клиент сервер
    authorized = False # Авторизация
    legacy_version = None # user-agent старого формата

    logger.info(f"Работаю с клиентом: {address[0]}")

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

            # Если пакет не содержит хотя бы заголовка, то обрываем соединение
            if len(data) < 44:
                break

            # Парсим заголовок
            unbuilded_header = await unbuild_header(data)
            payload = data[44:]

            # Обработка команд
            if unbuilded_header.get("command") == MRIM_CS_HELLO:
                # Приветствие клиента
                logger.info(f"Получил команду MRIM_CS_HELLO от клиента {address[0]}")
                
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
                logger.info(f"Отправил команду MRIM_CS_HELLO_ACK клиенту {address[0]}")
            elif unbuilded_header.get("command") == MRIM_CS_SSL:
                # Рукопожатие SSL
                logger.info(f"Получил команду MRIM_CS_SSL от клиента {address[0]}")
                
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
                logger.info(f"Отправил команду MRIM_CS_SSL_ACK клиенту {address[0]}")

                # Начинаем пиздец и ужас
                await writer.start_tls(context)
            elif unbuilded_header.get("command") == MRIM_CS_LOGIN2:
                # Обработка MRIM_CS_LOGIN2
                logger.info(f"Получил команду MRIM_CS_LOGIN2 от клиента {address[0]}")

                # Проверка приветствия и авторизации
                if greeted == False or authorized == True:
                    break

                # Выполняем авторизацию
                result_auth = await login2(writer, payload, unbuilded_header.get("magic"), unbuilded_header.get("proto"), unbuilded_header.get("seq"), connection, address)

                # Проверяем результат
                if result_auth.get("result") == "success":
                    email = result_auth.get("email")
                    authorized = True # Отмечаем в переменной авторизацию
                    legacy_version = result_auth.get("version2")
                    
                    await complete_auth(writer, unbuilded_header, address, email, connection, result_auth)
                else:
                    break
            elif unbuilded_header.get("command") == MRIM_CS_LOGIN3:
                # Обработка MRIM_CS_LOGIN3
                logger.info(f"Получил команду MRIM_CS_LOGIN3 от клиента {address[0]}")

                # Проверка приветствия и авторизации
                if greeted == False or authorized == True:
                    break

                # Выполняем авторизацию
                result_auth = await login3(writer, payload, unbuilded_header.get("magic"), unbuilded_header.get("proto"), unbuilded_header.get("seq"), connection, address)

                # Проверяем результат
                if result_auth.get("result") == "success":
                    email = result_auth.get("email")
                    authorized = True # Отмечаем в переменной авторизацию
                    legacy_version = result_auth.get("version2")
                    
                    await complete_auth(writer, unbuilded_header, address, email, connection, result_auth)
                else:
                    break
            elif unbuilded_header.get("command") == MRIM_CS_PING:
                # keep-alive
                logger.info(f"Получил команду MRIM_CS_PING от клиента {address[0]}")

                # Проверка приветствия
                if greeted == False:
                    break
            elif unbuilded_header.get("command") == MRIM_CS_CHANGE_STATUS:
                # Смена статуса
                logger.info(f"Получил команду MRIM_CS_CHANGE_STATUS от клиента {address[0]}")

                # Проверка приветствия и авторизации
                if greeted == False or authorized == False:
                    break

                await change_status(connection, address, email, payload, unbuilded_header.get("proto"))
            elif unbuilded_header.get("command") == MRIM_CS_WP_REQUEST:
                # Поиск
                logger.info(f"Получил команду MRIM_CS_WP_REQUEST от клиента {address[0]}")

                # Проверка приветствия и авторизации
                if greeted == False or authorized == False:
                    break

                await wp_request(writer, connection, address, payload, unbuilded_header.get("magic"), unbuilded_header.get("proto"), unbuilded_header.get("seq"))
            elif unbuilded_header.get("command") == MRIM_CS_ADD_CONTACT:
                # Добавление контакта
                logger.info(f"Получил команду MRIM_CS_ADD_CONTACT от клиента {address[0]}")

                # Проверка приветствия и авторизации
                if greeted == False or authorized == False:
                    break

                await add_contact(writer, connection, address, payload, unbuilded_header.get("magic"), unbuilded_header.get("proto"), unbuilded_header.get("seq"), email)
            elif unbuilded_header.get("command") == MRIM_CS_MODIFY_CONTACT:
                # Добавление контакта
                logger.info(f"Получил команду MRIM_CS_MODIFY_CONTACT от клиента {address[0]}")

                # Проверка приветствия и авторизации
                if greeted == False or authorized == False:
                    break
            elif unbuilded_header.get("command") == MRIM_CS_MESSAGE:
                # Пакет сообщения
                logger.info(f"Получил команду MRIM_CS_MESSAGE от клиента {address[0]}")

                # Проверка приветствия и авторизации
                if greeted == False or authorized == False:
                    break

                await new_message(writer, connection, address, payload, unbuilded_header.get("magic"), unbuilded_header.get("proto"), unbuilded_header.get("seq"), email, legacy_version)
            elif unbuilded_header.get("command") == MRIM_CS_MESSAGE_RECV:
                # Пакет о получении сообщения
                logger.info(f"Получил команду MRIM_CS_MESSAGE_RECV от клиента {address[0]}")

                # Проверка приветствия и авторизации
                if greeted == False or authorized == False:
                    break

                await recv_message(payload, unbuilded_header.get("proto"))
            elif unbuilded_header.get("command") == MRIM_CS_AUTHORIZE:
                # Авторизация контакта
                logger.info(f"Получил команду MRIM_CS_AUTHORIZE от клиента {address[0]}")

                # Проверка приветствия и авторизации
                if greeted == False or authorized == False:
                    break

                await authorize_contact(payload, connection, unbuilded_header.get("proto"), email)
            elif unbuilded_header.get("command") == MRIM_CS_GAME:
                # Игры
                logger.info(f"Получил команду MRIM_CS_GAME от клиента {address[0]}")

                # Проверка приветствия и авторизации
                if greeted == False or authorized == False:
                    break

                await games(payload, unbuilded_header.get("proto"), email)
            elif unbuilded_header.get("command") == MRIM_CS_SMS:
                # Отправка SMS
                logger.info(f"Получил команду MRIM_CS_SMS от клиента {address[0]}")

                # Проверка приветствия и авторизации
                if greeted == False or authorized == False:
                    break

                await send_sms(writer, address, payload, unbuilded_header.get("magic"), unbuilded_header.get("proto"), unbuilded_header.get("seq"), connection, email)
            elif unbuilded_header.get("command") == MRIM_CS_CALL:
                # Звонки
                logger.info(f"Получил команду MRIM_CS_CALL от клиента {address[0]}")

                # Проверка приветствия и авторизации
                if greeted == False or authorized == False:
                    break

                await call(payload, unbuilded_header.get("proto"), email)
            elif unbuilded_header.get("command") == MRIM_CS_CALL_ACK:
                # Звонки
                logger.info(f"Получил команду MRIM_CS_CALL_ACK от клиента {address[0]}")

                # Проверка приветствия и авторизации
                if greeted == False or authorized == False:
                    break

                await call_ack(payload, unbuilded_header.get("proto"), email)
            elif unbuilded_header.get("command") == MRIM_CS_FILE_TRANSFER:
                # Передача файлов
                logger.info(f"Получил команду MRIM_CS_FILE_TRANSFER от клиента {address[0]}")

                # Проверка приветствия и авторизации
                if greeted == False or authorized == False:
                    break

                await file_transfer(payload, unbuilded_header.get("proto"), email)
            elif unbuilded_header.get("command") == MRIM_CS_FILE_TRANSFER_ACK:
                # Передача файлов
                logger.info(f"Получил команду MRIM_CS_FILE_TRANSFER_ACK от клиента {address[0]}")

                # Проверка приветствия и авторизации
                if greeted == False or authorized == False:
                    break

                await file_transfer_ack(payload, unbuilded_header.get("proto"), email)
            else:
                logger.info(f"Неизвестная команда {hex(unbuilded_header.get('command'))}: {unbuilded_header};{payload}")
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
                                logger.info(f"Отправил пакет MRIM_CS_USER_STATUS пользователю {client.get('email')}")
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
                                logger.info(f"Отправил пакет MRIM_CS_USER_STATUS пользователю {client.get('email')}")

        # Закрываем подключение
        writer.close()
        await writer.wait_closed()
        connection.close()

        logger.info(f"Работа с клиентом {address[0]} завершена")

async def complete_auth(writer, unbuilded_header, address, email, connection, result_auth):
    """Завершение авторизации"""
    presence_setted = False # Установлен ли статус клиента в словаре

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
            presences[email]["com_support"] = 0x3FF
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

    # Собираем данные пакета
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
                logger.info(f"Отправил пакет MRIM_CS_USER_STATUS пользователю {client.get('email')}")    

async def main():
    """Главная функция сервера"""
    server = await asyncio.start_server(handle_client, host, port)
    
    async with server:
        logger.info(f"MRIM-сервер запущен на портах {os.environ.get('redirect_port')} // {os.environ.get('main_port')} // {os.environ.get("avatars_port")}")
        await server.serve_forever()
