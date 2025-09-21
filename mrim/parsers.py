# -*- coding: utf-8 -*-

# OMRA by Starwear

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
        password = data[password_start:password_end].decode("windows-1251")
        
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
    elif proto in [65551]:
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
            "language": language
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
    elif proto in [65556]:
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
            "status": status,
            "xstatus_meaning": xstatus_meaning,
            "xstatus_title": xstatus_title,
            "xstatus_description": xstatus_description,
            "com_support": com_support,
            "version1": version1,
            "version2": version2,
            "language": language
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
    elif proto in [65559]:
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