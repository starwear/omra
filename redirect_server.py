# -*- coding: utf-8 -*-

# OMRA by PostDevelopers

# Импортируем библиотеки
import asyncio, os, logging
from dotenv import load_dotenv

# Настройка логирования
logger = logging.getLogger("omra_redirect")
logging.basicConfig(level=logging.INFO)

# Загрузка конфигурации
load_dotenv()

# Настройка сервера
host = os.environ.get("redirect_host") # Хост
port = os.environ.get("redirect_port") # Порт

main_host = os.environ.get("main_host") # Хост главного сервера
main_port = os.environ.get("main_port") # Порт главного сервера

async def handle_client(reader, writer):
    """Функция обработки подключений"""
    # Получение адреса подключения
    address = writer.get_extra_info("peername")

    logger.info("Работаю с клиентом: {}".format(address))

    try:
        writer.write("{}:{}\n".format(main_host, main_port).encode("windows-1251"))
        await writer.drain()
        writer.close()
    except Exception as error:
        logger.info("Произошла ошибка: {}".format(error))
    finally:
        writer.close()
        await writer.wait_closed()
        logger.info("Работа с клиентом {} завершена".format(address))

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