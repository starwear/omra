# -*- coding: utf-8 -*-

# OMRA by Starwear

import hashlib

async def login3_parser(data, proto):
    """Парсер MRIM_CS_LOGIN3"""
    if proto in [65557]:
        # Извлечение почты
        email_length = int.from_bytes(data[0:4], "little")
        email_start = 4
        email_end = email_start + email_length
        email = data[email_start:email_end].decode("windows-1251")

        # Извлечение пароля
        password_length = int.from_bytes(data[email_end:email_end + 4], "little")
        password_start = email_end + 4
        password_end = password_start + password_length
        password = hashlib.md5(data[password_start:password_end].decode("windows-1251").encode("windows-1251")).hexdigest()
        
        # Извлечение DWORD ???
        unknown_dword1_start = password_end
        unknown_dword1_end = password_end + 4
        unknown_dword1 = int.from_bytes(data[unknown_dword1_start:unknown_dword1_end], "little")

        # Извлечение 1 версии
        version1_length = int.from_bytes(data[unknown_dword1_end:unknown_dword1_end + 4], "little")
        version1_start = unknown_dword1_end + 4
        version1_end = version1_start + version1_length
        version1 = data[version1_start:version1_end].decode("windows-1251")

        # Извлечение локализации
        locale_length = int.from_bytes(data[version1_end:version1_end + 4], "little")
        locale_start = version1_end + 4
        locale_end = locale_start + locale_length
        locale = data[locale_start:locale_end].decode("windows-1251")

        # Извлечение DWORD ???
        unknown_dword2_start = locale_end
        unknown_dword2_end = locale_end + 4
        unknown_dword2 = int.from_bytes(data[unknown_dword2_start:unknown_dword2_end], "little")

        # Извлечение DWORD ???
        unknown_dword3_start = unknown_dword2_end
        unknown_dword3_end = unknown_dword2_end + 4
        unknown_dword3 = int.from_bytes(data[unknown_dword3_start:unknown_dword3_end], "little")

        # geo-list ???
        geolist_length = int.from_bytes(data[unknown_dword3_end:unknown_dword3_end + 4], "little")
        geolist_start = unknown_dword3_end + 4
        geolist_end = geolist_start + geolist_length
        geolist = data[geolist_start:geolist_end].decode("windows-1251")

        # Извлечение 2 версии
        version2_length = int.from_bytes(data[geolist_end:geolist_end + 4], "little")
        version2_start = geolist_end + 4
        version2_end = version2_start + version2_length
        version2 = data[version2_start:version2_end].decode("windows-1251")

        # Возвращаем
        return {
            "email": email,
            "password": password,
            "version1": version1,
            "version2": version2
        }
    elif proto in [65558, 65559]:
        # Извлечение почты
        email_length = int.from_bytes(data[0:4], "little")
        email_start = 4
        email_end = email_start + email_length
        email = data[email_start:email_end].decode("windows-1251")

        # Извлечение пароля
        password_length = int.from_bytes(data[email_end:email_end + 4], "little")
        password_start = email_end + 4
        password_end = password_start + password_length
        password = data[password_start:password_end].hex()

        # Извлечение DWORD ???
        unknown_dword1_start = password_end
        unknown_dword1_end = password_end + 4
        unknown_dword1 = int.from_bytes(data[unknown_dword1_start:unknown_dword1_end], "little")
        # Извлечение 1 версии
        version1_length = int.from_bytes(data[unknown_dword1_end:unknown_dword1_end + 4], "little")
        version1_start = unknown_dword1_end + 4
        version1_end = version1_start + version1_length
        version1 = data[version1_start:version1_end].decode("windows-1251")

        # Извлечение локализации
        locale_length = int.from_bytes(data[version1_end:version1_end + 4], "little")
        locale_start = version1_end + 4
        locale_end = locale_start + locale_length
        locale = data[locale_start:locale_end].decode("windows-1251")

        # Извлечение DWORD ???
        unknown_dword2_start = locale_end
        unknown_dword2_end = locale_end + 4
        unknown_dword2 = int.from_bytes(data[unknown_dword2_start:unknown_dword2_end], "little")

        # Извлечение DWORD ???
        unknown_dword3_start = unknown_dword2_end
        unknown_dword3_end = unknown_dword2_end + 4
        unknown_dword3 = int.from_bytes(data[unknown_dword3_start:unknown_dword3_end], "little")

        # geo-list ???
        geolist_length = int.from_bytes(data[unknown_dword3_end:unknown_dword3_end + 4], "little")
        geolist_start = unknown_dword3_end + 4
        geolist_end = geolist_start + geolist_length
        geolist = data[geolist_start:geolist_end].decode("windows-1251")

        # Извлечение 2 версии
        version2_length = int.from_bytes(data[geolist_end:geolist_end + 4], "little")
        version2_start = geolist_end + 4
        version2_end = version2_start + version2_length
        version2 = data[version2_start:version2_end].decode("windows-1251")

        # Возвращаем
        return {
            "email": email,
            "password": password,
            "version1": version1,
            "version2": version2
        }
    else:
        # Извлечение почты
        email_length = int.from_bytes(data[0:4], "little")
        email_start = 4
        email_end = email_start + email_length
        email = data[email_start:email_end].decode("windows-1251")

        # Извлечение пароля
        password_length = int.from_bytes(data[email_end:email_end + 4], "little")
        password_start = email_end + 4
        password_end = password_start + password_length
        password = data[password_start:password_end].hex()

        # Извлечение DWORD ???
        unknown_dword1_start = password_end
        unknown_dword1_end = password_end + 4
        unknown_dword1 = int.from_bytes(data[unknown_dword1_start:unknown_dword1_end], "little")
        # Извлечение 1 версии
        version1_length = int.from_bytes(data[unknown_dword1_end:unknown_dword1_end + 4], "little")
        version1_start = unknown_dword1_end + 4
        version1_end = version1_start + version1_length
        version1 = data[version1_start:version1_end].decode("windows-1251")

        # Извлечение локализации
        locale_length = int.from_bytes(data[version1_end:version1_end + 4], "little")
        locale_start = version1_end + 4
        locale_end = locale_start + locale_length
        locale = data[locale_start:locale_end].decode("windows-1251")

        # Извлечение DWORD ???
        unknown_dword2_start = locale_end
        unknown_dword2_end = locale_end + 4
        unknown_dword2 = int.from_bytes(data[unknown_dword2_start:unknown_dword2_end], "little")

        # Извлечение DWORD ???
        unknown_dword3_start = unknown_dword2_end
        unknown_dword3_end = unknown_dword2_end + 4
        unknown_dword3 = int.from_bytes(data[unknown_dword3_start:unknown_dword3_end], "little")

        # geo-list ???
        geolist_length = int.from_bytes(data[unknown_dword3_end:unknown_dword3_end + 4], "little")
        geolist_start = unknown_dword3_end + 4
        geolist_end = geolist_start + geolist_length
        geolist = data[geolist_start:geolist_end].decode("windows-1251")

        # Извлечение 2 версии
        version2_length = int.from_bytes(data[geolist_end:geolist_end + 4], "little")
        version2_start = geolist_end + 4
        version2_end = version2_start + version2_length
        version2 = data[version2_start:version2_end].decode("windows-1251")

        # Возвращаем
        return {
            "email": email,
            "password": password,
            "version1": version1,
            "version2": version2
        }

async def login2_parser(data, proto):
    """Парсер MRIM_CS_LOGIN2"""
    if proto in [65543, 65544, 65545, 65546, 65547, 65548, 65549]:
        # Извлечение почты
        email_length = int.from_bytes(data[0:4], "little")
        email_start = 4
        email_end = email_start + email_length
        email = data[email_start:email_end].decode("windows-1251")

        # Извлечение пароля
        password_length = int.from_bytes(data[email_end:email_end + 4], "little")
        password_start = email_end + 4
        password_end = password_start + password_length
        password = data[password_start:password_end].decode("windows-1251")

        # Извлечение статуса
        status_start = password_end
        status_end = password_end + 4
        status = int.from_bytes(data[status_start:status_end], "little")

        # Извлечение юзер-агента
        user_agent_length = int.from_bytes(data[status_end:status_end + 4], "little")
        user_agent_start = status_end + 4
        user_agent_end = user_agent_start + user_agent_length
        user_agent = data[user_agent_start:user_agent_end].decode("windows-1251")
    
        # Возвращаем
        return {
            "email": email,
            "password": password,
            "status": status,
            "xstatus_meaning": "",
            "xstatus_title": "",
            "xstatus_description": "",
            "com_support": 0,
            "version1": "",
            "version2": user_agent,
            "language": "ru"
        }
    elif proto in [65550, 65551]:
        # Извлечение почты
        email_length = int.from_bytes(data[0:4], "little")
        email_start = 4
        email_end = email_start + email_length
        email = data[email_start:email_end].decode("windows-1251")

        # Извлечение пароля
        password_length = int.from_bytes(data[email_end:email_end + 4], "little")
        password_start = email_end + 4
        password_end = password_start + password_length
        password = data[password_start:password_end].decode("windows-1251")

        # Извлечение статуса цифрой
        status = int.from_bytes(data[password_end:password_end + 4], "little")

        # Извлечение значения хстатуса
        xstatus_meaning_length = int.from_bytes(data[password_end + 4:password_end + 8], "little")
        xstatus_meaning_start = password_end + 8
        xstatus_meaning_end = xstatus_meaning_start + xstatus_meaning_length
        xstatus_meaning = data[xstatus_meaning_start:xstatus_meaning_end].decode("windows-1251")

        # Извлечение заголовка хстатуса
        xstatus_title_length = int.from_bytes(data[xstatus_meaning_end:xstatus_meaning_end + 4], "little")
        xstatus_title_start = xstatus_meaning_end + 4
        xstatus_title_end = xstatus_title_start + xstatus_title_length
        xstatus_title = data[xstatus_title_start:xstatus_title_end].decode("windows-1251")

        # Извлечение описания хстатуса
        xstatus_description_length = int.from_bytes(data[xstatus_title_end:xstatus_title_end + 4], "little")
        xstatus_description_start = xstatus_title_end + 4
        xstatus_description_end = xstatus_description_start + xstatus_description_length
        xstatus_description = data[xstatus_description_start:xstatus_description_end].decode("windows-1251")

        # Извлечение com_support
        com_support = int.from_bytes(data[xstatus_description_end:xstatus_description_end + 4], "little")

        # Извлекаем 1 версию
        version1_length = int.from_bytes(data[xstatus_description_end + 4:xstatus_description_end + 8], "little")
        version1_start = xstatus_description_end + 8
        version1_end = version1_start + version1_length
        version1 = data[version1_start:version1_end].decode("windows-1251")

        # Извлекаем 2 версию
        version2_length = int.from_bytes(data[version1_end:version1_end + 4], "little")
        version2_start = version1_end + 4
        version2_end = version2_start + version2_length
        version2 = data[version2_start:version2_end].decode("windows-1251")
        
        # Возвращаем
        return {
            "email": email,
            "password": password,
            "status": status,
            "xstatus_meaning": xstatus_meaning,
            "xstatus_title": xstatus_title,
            "xstatus_description": xstatus_description,
            "com_support": com_support,
            "version1": version1,
            "version2": version2,
            "language": "ru"
        }
    elif proto in [65552, 65554, 65555]:
        # Извлечение почты
        email_length = int.from_bytes(data[0:4], "little")
        email_start = 4
        email_end = email_start + email_length
        email = data[email_start:email_end].decode("windows-1251")

        # Извлечение пароля
        password_length = int.from_bytes(data[email_end:email_end + 4], "little")
        password_start = email_end + 4
        password_end = password_start + password_length
        password = data[password_start:password_end].decode("windows-1251")

        # Извлечение статуса цифрой
        status = int.from_bytes(data[password_end:password_end + 4], "little")

        # Извлечение значения хстатуса
        xstatus_meaning_length = int.from_bytes(data[password_end + 4:password_end + 8], "little")
        xstatus_meaning_start = password_end + 8
        xstatus_meaning_end = xstatus_meaning_start + xstatus_meaning_length
        xstatus_meaning = data[xstatus_meaning_start:xstatus_meaning_end].decode("windows-1251")

        # Извлечение заголовка хстатуса
        xstatus_title_length = int.from_bytes(data[xstatus_meaning_end:xstatus_meaning_end + 4], "little")
        xstatus_title_start = xstatus_meaning_end + 4
        xstatus_title_end = xstatus_title_start + xstatus_title_length
        xstatus_title = data[xstatus_title_start:xstatus_title_end].decode("utf-16-le")

        # Извлечение описания хстатуса
        xstatus_description_length = int.from_bytes(data[xstatus_title_end:xstatus_title_end + 4], "little")
        xstatus_description_start = xstatus_title_end + 4
        xstatus_description_end = xstatus_description_start + xstatus_description_length
        xstatus_description = data[xstatus_description_start:xstatus_description_end].decode("utf-16-le")

        # Извлечение com_support
        com_support = int.from_bytes(data[xstatus_description_end:xstatus_description_end + 4], "little")

        # Извлекаем 1 версию
        version1_length = int.from_bytes(data[xstatus_description_end + 4:xstatus_description_end + 8], "little")
        version1_start = xstatus_description_end + 8
        version1_end = version1_start + version1_length
        version1 = data[version1_start:version1_end].decode("windows-1251")

        # Извлечение языка
        language_length = int.from_bytes(data[version1_end:version1_end + 4], "little")
        language_start = version1_end + 4
        language_end = language_start + language_length
        language = data[language_start:language_end].decode("windows-1251")

        # Извлекаем 2 версию
        version2_length = int.from_bytes(data[language_end:language_end + 4], "little")
        version2_start = language_end + 4
        version2_end = version2_start + version2_length
        version2 = data[version2_start:version2_end].decode("windows-1251")

        # Возвращаем
        return {
            "email": email,
            "password": password,
            "status": status,
            "xstatus_meaning": xstatus_meaning,
            "xstatus_title": xstatus_title,
            "xstatus_description": xstatus_description,
            "com_support": com_support,
            "version1": version1,
            "version2": version2,
            "language": language
        }
    elif proto in [65556, 65557]:
        # Извлечение почты
        email_length = int.from_bytes(data[0:4], "little")
        email_start = 4
        email_end = email_start + email_length
        email = data[email_start:email_end].decode("windows-1251")

        # Извлечение пароля
        password_length = int.from_bytes(data[email_end:email_end + 4], "little")
        password_start = email_end + 4
        password_end = password_start + password_length
        password = data[password_start:password_end].decode("windows-1251")

        # Извлечение статуса цифрой
        status = int.from_bytes(data[password_end:password_end + 4], "little")

        # Извлечение значения хстатуса
        xstatus_meaning_length = int.from_bytes(data[password_end + 4:password_end + 8], "little")
        xstatus_meaning_start = password_end + 8
        xstatus_meaning_end = xstatus_meaning_start + xstatus_meaning_length
        xstatus_meaning = data[xstatus_meaning_start:xstatus_meaning_end].decode("windows-1251")

        # Извлечение заголовка хстатуса
        xstatus_title_length = int.from_bytes(data[xstatus_meaning_end:xstatus_meaning_end + 4], "little")
        xstatus_title_start = xstatus_meaning_end + 4
        xstatus_title_end = xstatus_title_start + xstatus_title_length
        xstatus_title = data[xstatus_title_start:xstatus_title_end].decode("utf-16-le")

        # Извлечение описания хстатуса
        xstatus_description_length = int.from_bytes(data[xstatus_title_end:xstatus_title_end + 4], "little")
        xstatus_description_start = xstatus_title_end + 4
        xstatus_description_end = xstatus_description_start + xstatus_description_length
        xstatus_description = data[xstatus_description_start:xstatus_description_end].decode("utf-16-le")

        # Извлечение com_support
        com_support = int.from_bytes(data[xstatus_description_end:xstatus_description_end + 4], "little")

        # Извлекаем 1 версию
        version1_length = int.from_bytes(data[xstatus_description_end + 4:xstatus_description_end + 8], "little")
        version1_start = xstatus_description_end + 8
        version1_end = version1_start + version1_length
        version1 = data[version1_start:version1_end].decode("windows-1251")

        # Извлечение языка
        language_length = int.from_bytes(data[version1_end:version1_end + 4], "little")
        language_start = version1_end + 4
        language_end = language_start + language_length
        language = data[language_start:language_end].decode("windows-1251")

        # Извлекаем 2 версию
        version2_length = int.from_bytes(data[language_end + 8:language_end + 12], "little")
        version2_start = language_end + 12
        version2_end = version2_start + version2_length
        version2 = data[version2_start:version2_end].decode("windows-1251")

        # Возвращаем
        return {
            "email": email,
            "password": password,
            "status": status,
            "xstatus_meaning": xstatus_meaning,
            "xstatus_title": xstatus_title,
            "xstatus_description": xstatus_description,
            "com_support": com_support,
            "version1": version1,
            "version2": version2,
            "language": language
        }
    else:
        # Извлечение почты
        email_length = int.from_bytes(data[0:4], "little")
        email_start = 4
        email_end = email_start + email_length
        email = data[email_start:email_end].decode("windows-1251")

        # Извлечение пароля
        password_length = int.from_bytes(data[email_end:email_end + 4], "little")
        password_start = email_end + 4
        password_end = password_start + password_length
        password = data[password_start:password_end].decode("windows-1251")

        # Извлечение статуса
        status_start = password_end
        status_end = password_end + 4
        status = int.from_bytes(data[status_start:status_end], "little")

        # Извлечение юзер-агента
        user_agent_length = int.from_bytes(data[status_end:status_end + 4], "little")
        user_agent_start = status_end + 4
        user_agent_end = user_agent_start + user_agent_length
        user_agent = data[user_agent_start:user_agent_end].decode("windows-1251")

        # Возвращаем
        return {
            "email": email,
            "password": password,
            "status": 1,
            "xstatus_meaning": "",
            "xstatus_title": "",
            "xstatus_description": "",
            "com_support": 0,
            "version1": "",
            "version2": "Unrecognized MRA",
            "language": "ru"
        }
    
async def change_status_parser(data, proto):
    """Парсер MRIM_CS_CHANGE_STATUS"""
    if proto in [65543, 65544, 65545, 65546, 65547, 65548, 65549]:
        # Извлекаем числовой статус
        status = int.from_bytes(data[0:4], "little")

        # Возвращаем
        return {
            "status": status,
            "xstatus_meaning": "",
            "xstatus_title": "",
            "xstatus_description": "",
            "com_support": 0
        }
    elif proto in [65550, 65551]:
        # Извлекаем числовой статус
        status = int.from_bytes(data[0:4], "little")

        # Извлекаем длину значения хстатуса
        xstatus_meaning_length = int.from_bytes(data[4:8], "little")

        # Извлекаем значение хстатуса
        xstatus_meaning_start = 8
        xstatus_meaning_end = xstatus_meaning_start + xstatus_meaning_length
        xstatus_meaning = data[xstatus_meaning_start:xstatus_meaning_end].decode('windows-1251')

        # Извлечение длины заголовка хстатуса 
        xstatus_title_length = int.from_bytes(data[xstatus_meaning_end:xstatus_meaning_end + 4], "little")

        # Извлечение заголовка статуса
        xstatus_title_start = xstatus_meaning_end + 4
        xstatus_title_end = xstatus_title_start + xstatus_title_length
        xstatus_title = data[xstatus_title_start:xstatus_title_end].decode('windows-1251')

        # Извлечение длины описания хстатуса
        xstatus_description_length = int.from_bytes(data[xstatus_title_end:xstatus_title_end + 4], "little")

        # Извлечение описания хстатуса
        xstatus_description_start = xstatus_title_end + 4
        xstatus_description_end = xstatus_description_start + xstatus_description_length
        xstatus_description = data[xstatus_description_start:xstatus_description_end].decode('windows-1251')

        # com_support
        com_support = int.from_bytes(data[xstatus_description_end:xstatus_description_end + 4], "little")

        # Возвращаем
        return {
            "status": status,
            "xstatus_meaning": xstatus_meaning,
            "xstatus_title": xstatus_title,
            "xstatus_description": xstatus_description,
            "com_support": com_support
        }
    elif proto in [65552, 65554, 65555, 65556, 65557, 65558, 65559]:
        # Извлекаем числовой статус
        status = int.from_bytes(data[0:4], "little")

        # Извлекаем длину значения хстатуса
        xstatus_meaning_length = int.from_bytes(data[4:8], "little")

        # Извлекаем значение хстатуса
        xstatus_meaning_start = 8
        xstatus_meaning_end = xstatus_meaning_start + xstatus_meaning_length
        xstatus_meaning = data[xstatus_meaning_start:xstatus_meaning_end].decode('windows-1251')

        # Извлечение длины заголовка хстатуса 
        xstatus_title_length = int.from_bytes(data[xstatus_meaning_end:xstatus_meaning_end + 4], "little")

        # Извлечение заголовка статуса
        xstatus_title_start = xstatus_meaning_end + 4
        xstatus_title_end = xstatus_title_start + xstatus_title_length
        xstatus_title = data[xstatus_title_start:xstatus_title_end].decode("utf-16-le")

        # Извлечение длины описания хстатуса
        xstatus_description_length = int.from_bytes(data[xstatus_title_end:xstatus_title_end + 4], "little")

        # Извлечение описания хстатуса
        xstatus_description_start = xstatus_title_end + 4
        xstatus_description_end = xstatus_description_start + xstatus_description_length
        xstatus_description = data[xstatus_description_start:xstatus_description_end].decode("utf-16-le")

        # com_support
        com_support = int.from_bytes(data[xstatus_description_end:xstatus_description_end + 4], "little")

        # Возвращаем
        return {
            "status": status,
            "xstatus_meaning": xstatus_meaning,
            "xstatus_title": xstatus_title,
            "xstatus_description": xstatus_description,
            "com_support": com_support
        }
    else:
        # Извлекаем числовой статус
        status = int.from_bytes(data[0:4], "little")

        # Возвращаем
        return {
            "status": status,
            "xstatus_meaning": "",
            "xstatus_title": "",
            "xstatus_description": "",
            "com_support": 0
        }

async def wp_request_parser(data, proto):
    """Парсер MRIM_CS_WP_REQUEST"""
    offset = 0
    result = []

    for _ in range(2):
        field = int.from_bytes(data[offset:offset+4], "little")
        offset += 4

        value_length = int.from_bytes(data[offset:offset+4], "little")
        offset += 4

        value_start = offset 
        value_end = value_start + value_length
        value = data[value_start:value_end]
        offset += value_length

        result.append(
            {
                "field": field,
                "value": value.decode("windows-1251")
            }
        )

    return result

async def add_contact_parser(data, proto):
    flags = int.from_bytes(data[0:4], "little")
    group_id = int.from_bytes(data[4:8], "little")

    contact_length = int.from_bytes(data[8:12], "little")
    contact_start = 12
    contact_end = contact_start + contact_length
    contact = data[contact_start:contact_end].decode("windows-1251")

    name_length = int.from_bytes(data[contact_end:contact_end + 4], "little")
    name_start = contact_end + 4
    name_end = name_start + name_length
    if proto in [65552, 65554, 65555, 65556, 65557, 65558, 65559]:
        name = data[name_start:name_end].decode("utf-16-le")
    else:
        name = data[name_start:name_end].decode("windows-1251")

    unused_length = int.from_bytes(data[name_end:name_end + 4], "little")
    unused_start = name_end + 4
    unused_end = unused_start + unused_length
    unused = data[unused_start:unused_end].decode("windows-1251")

    return {
        "flags": flags,
        "group_id": group_id,
        "contact": contact,
        "name": name,
        "unused": unused
    }

async def modify_contact_parser(data, proto):
    """Парсер MRIM_CS_MODIFY_CONTACT"""
    # Айди (???)
    id = int.from_bytes(data[0:4], "little")

    # Флаги
    flags = int.from_bytes(data[4:8], "little")

    # Извлечение айди группы
    group_id = int.from_bytes(data[8:12], "little")

    # Извлечение почты (имени)
    email_length = int.from_bytes(data[12:16], "little")
    email_start = 16
    email_end = email_start + email_length
    email = data[email_start:email_end].decode("windows-1251")

    # Извлечение имени
    name_length = int.from_bytes(data[email_end:email_end + 4], "little")
    name_start = email_end + 4
    name_end = name_start + name_length
    name = data[name_start:name_end].decode("windows-1251")

    # Извлечение мобил, наверное
    phones_length = int.from_bytes(data[name_end:name_end + 4], "little")
    phones_start = name_end + 4
    phones_end = phones_start + phones_length
    phones = data[phones_start:phones_end].decode("windows-1251")

    # Возвращаем
    return {
        "id": id,
        "flags": flags,
        "group_id": group_id,
        "email": email,
        "name": name,
        "phones": phones
    }

async def new_message_parser(data, proto):
    """Парсер MRIM_CS_MESSAGE"""
    # Флаги сообщения
    flags = int.from_bytes(data[0:4], "little")

    # Получатель сообщения
    to_length = int.from_bytes(data[4:8], "little")
    to_start = 8
    to_end = to_start + to_length
    to = data[to_start:to_end].decode("windows-1251")   

    # Само сообщение
    message_length = int.from_bytes(data[to_end:to_end + 4], "little")
    message_start = to_end + 4
    message_end = message_start + message_length

    if proto in [65552, 65554, 65555, 65556, 65557, 65558, 65559]:
        if flags in [12]:
            message = data[message_start:message_end].decode("windows-1251")
        else:
            try:
                message = data[message_start:message_end].decode("utf-16-le")
            except:
                message = data[message_start:message_end].decode("windows-1251")
    else:
        message = data[message_start:message_end].decode("windows-1251")

    # Сообщение в формате RTF
    rtf_message_length = int.from_bytes(data[message_end:message_end + 4], "little")
    rtf_message_start = message_end + 4
    rtf_message_end = rtf_message_start + rtf_message_length
    rtf_message = data[rtf_message_start:rtf_message_end].decode("windows-1251")

    # Возвращаем
    return {
        "flags": flags,
        "to": to,
        "message": message,
        "rtf_message": rtf_message
    }

async def recv_message_parser(data, proto):
    """Парсер MRIM_CS_MESSAGE_RECV"""
    # Отправитель сообщения
    from_msg_length = int.from_bytes(data[0:4], "little")
    from_msg_start = 4
    from_msg_end = from_msg_start + from_msg_length
    from_msg = data[from_msg_start:from_msg_end].decode("windows-1251")

    # seq сообщения
    msg_id = int.from_bytes(data[from_msg_end:from_msg_end + 4], "little")

    return {
        "from": from_msg,
        "msg_id": msg_id
    }

async def authorize_parser(data, proto):
    """Парсер пакета MRIM_CS_AUTHORIZE"""
    # Извлечение пользователя
    user_length = int.from_bytes(data[0:4], "little")
    user_start = 4
    user_end = user_start + user_length
    user = data[user_start:user_end].decode("windows-1251")

    # Возвращаем
    return {
        "user": user
    }

async def games_parser(data, proto):
    offset = 0

    # Извлечение почты, кому адресован пакет
    email_length = int.from_bytes(data[0:4], "little")
    email_start = 4
    email_end = email_start + email_length
    email = data[email_start:email_end].decode("windows-1251")

    offset += email_end

    # Уникальный ID сессии
    session_id = int.from_bytes(data[offset:offset + 4], "little")
    offset += 4

    # Сообщение
    game_msg = int.from_bytes(data[offset:offset + 4], "little")
    offset += 4

    # ID сообщения
    msg_id = int.from_bytes(data[offset:offset + 4], "little")
    offset += 4

    # Время отправки
    time_send = int.from_bytes(data[offset:offset + 4], "little")
    offset += 4

    # Игровые данные
    game_data = data[offset:]

    # Возвращение пропаршенных данных
    return {
        "email": email,
        "session_id": session_id,
        "game_msg": game_msg,
        "msg_id": msg_id,
        "time_send": time_send,
        "game_data": game_data
    }

async def sms_parser(data, proto):
    """Парсер MRIM_CS_SMS"""
    # Извлечение флагов
    flags = int.from_bytes(data[0:4], "little")

    # Извлечение телефона
    phone_length = int.from_bytes(data[4:8], "little")
    phone_start = 8
    phone_end = phone_start + phone_length
    phone = data[phone_start:phone_end].decode("windows-1251")

    # Извлечение сообщения
    message_length = int.from_bytes(data[phone_end:phone_end + 4], "little")
    message_start = phone_end + 4
    message_end = message_start + message_length
    if proto in [65552, 65554, 65555, 65556, 65557, 65558, 65559]:
        message = data[message_start:message_end].decode("utf-16-le")
    else:
        message = data[message_start:message_end].decode("windows-1251")

    # Возвращаем пропаршенные данные
    return {
        "flags": flags,
        "phone": phone,
        "message": message
    }

async def call_parser(data, proto):
    """Парсер MRIM_CS_CALL"""

    # Извлекаем почту
    email_length = int.from_bytes(data[0:4], "little")
    email_start = 4
    email_end = email_start + email_length
    email = data[email_start:email_end].decode("windows-1251")

    # ID передачи
    transfer_id = int.from_bytes(data[email_end:email_end + 4], "little")

    # Айпи адреса для p2p
    connection_address_length = int.from_bytes(data[email_end:email_end + 8], "little")
    connection_address_start = email_end + 8
    connection_address_end = connection_address_start + connection_address_length
    connection_address = data[connection_address_start:connection_address_end].decode("windows-1251")

    return {
        "email": email,
        "transfer_id": transfer_id,
        "ips": connection_address
    }

async def call_ack_parser(data, proto):
    """Парсер MRIM_CS_CALL_ACK"""
    call_status = int.from_bytes(data[0:4], "little")

    email_length = int.from_bytes(data[4:8], "little")
    email_start = 8
    email_end = email_start + email_length
    email = data[email_start:email_end].decode("windows-1251")

    transfer_id = int.from_bytes(data[email_end:email_end + 4], "little")

    return {
        "call_status": call_status,
        "email": email,
        "transfer_id": transfer_id
    }

async def file_transfer_parser(data, proto):
    """Парсер MRIM_CS_FILE_TRANSFER"""
    # Почта
    email_length = int.from_bytes(data[0:4], "little")
    email_start = 4
    email_end = email_start + email_length
    email = data[email_start:email_end].decode("windows-1251")

    # ID передачи
    transfer_id = int.from_bytes(data[email_end:email_end + 4], "little")

    # Суммарный размер всех файлов, которые нужно передать
    total_size = int.from_bytes(data[email_end + 4:email_end + 8], "little")

    # 3 этажный лпс мутантоподобный
    floor_lps_length = int.from_bytes(data[email_end + 8:email_end + 12], "little")
    floor_lps_start = email_end + 12
    floor_lps_end = floor_lps_start + floor_lps_length
    floor_lps = data[floor_lps_start:floor_lps_end]

    # Описание всех передаваемых файлов
    file_desc_length = int.from_bytes(data[email_end + 12:email_end + 16], "little")
    file_desc_start = email_end + 16
    file_desc_end = file_desc_start + file_desc_length
    file_desc = data[file_desc_start:file_desc_end].decode("windows-1251")

    # Пустой параметр
    empty_param_length = int.from_bytes(data[file_desc_end:file_desc_end + 4], "little")
    empty_param_start = file_desc_end + 4
    empty_param_end = empty_param_start + empty_param_length
    empty_param = data[empty_param_start:empty_param_end].decode("windows-1251")

    # IP для p2p
    connection_address_length = int.from_bytes(data[empty_param_end:empty_param_end + 8], "little")
    connection_address_start = empty_param_end + 8
    connection_address_end = connection_address_start + connection_address_length
    connection_address = data[connection_address_start:connection_address_end].decode("windows-1251")

    return {
        "email": email,
        "transfer_id": transfer_id,
        "total_size": total_size,
        "file_desc": file_desc,
        "empty_param": empty_param,
        "connection_address": connection_address
    }

async def file_transfer_ack_parser(data, proto):
    """Парсер MRIM_CS_FILE_TRANSFER_ACK"""
    # Статус
    status = int.from_bytes(data[0:4], "little")

    # Кому пакет адресован
    email_length = int.from_bytes(data[4:8], "little")
    email_start = 8
    email_end = email_start + email_length
    email = data[email_start:email_end].decode("windows-1251")

    # ID передачи
    transfer_id = int.from_bytes(data[email_end:email_end + 4], "little")

    # Адреса зеркал
    mirror_address_length = int.from_bytes(data[email_end + 4:email_end + 8], "little")
    mirror_address_start = email_end + 4
    mirror_address_end = mirror_address_start + mirror_address_length
    mirror_address = data[mirror_address_start:mirror_address_end].decode("windows-1251")

    return {
        "status": status,
        "email": email,
        "transfer_id": transfer_id,
        "mirror_address": mirror_address
    }

async def microblog_change_parser(data, proto):
    """Парсер MRIM_CS_CHANGE_USER_BLOG_STATUS"""
    # Извлечение флагов
    flags = int.from_bytes(data[0:4], "little")

    # Извлечение текста сообщения
    message_length = int.from_bytes(data[4:8], "little")
    message_start = 8
    message_end = message_start + message_length
    message = data[message_start:message_end].decode("utf-16-le")

    # Возвращаем
    return {
        "flags": flags,
        "message": message
    }