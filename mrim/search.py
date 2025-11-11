# -*- coding: utf-8 -*-

# OMRA by Starwear

# Импортируем библиотеки
import aiomysql, time

# Импортируем реализацию
from mrim.parsers import wp_request_parser
from mrim.proto_types import create_lps, create_ul, build_header
from mrim.proto import MRIM_CS_ANKETA_INFO, MRIM_CS_WP_REQUEST_PARAM_USER, MRIM_CS_WP_REQUEST_PARAM_DOMAIN, MRIM_ANKETA_INFO_STATUS_OK, MRIM_ANKETA_INFO_STATUS_NOUSER
from main import logger

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
    
    email = f"{email_parts.get('login')}@{email_parts.get('domain')}"

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
