# -*- coding: utf-8 -*-

# OMRA by Starwear

# Импортируем библиотеки
import base64

# Импортируем реализацию
from mrim.parsers import new_message_parser, recv_message_parser
from mrim.proto_types import create_lps, create_ul, build_header
from mrim.proto import MRIM_CS_MESSAGE_ACK, MESSAGE_FLAG_NOTIFY, MRIM_CS_MESSAGE_STATUS, MESSAGE_REJECTED_DENY_OFFMSG, MESSAGE_DELIVERED
from main import clients, logger

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
                            logger.info(f"Отправил команду MRIM_CS_MESSAGE_ACK клиенту {client.get('email')}")

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
            logger.info(f"Отправил команду MRIM_CS_MESSAGE_ACK клиенту {client.get('email')}")
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
        logger.info(f"Отправил команду MRIM_CS_MESSAGE_STATUS клиенту {address[0]}")

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
            logger.info(f"Отправил команду MRIM_CS_MESSAGE_STATUS клиенту {client.get('email')}")
