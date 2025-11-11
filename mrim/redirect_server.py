# -*- coding: utf-8 -*-

# OMRA by Starwear

# Импортируем библиотеки
import asyncio, os
from dotenv import load_dotenv

# Загрузка конфигурации
load_dotenv()

# Настройка сервера
host = os.environ.get("redirect_host") # Хост
port = os.environ.get("redirect_port") # Порт

main_host = os.environ.get("main_host") # Хост главного сервера
main_port = os.environ.get("main_port") # Порт главного сервера

async def handle_client(reader, writer):
    """Функция обработки подключений"""
    try:
        writer.write(f"{main_host}:{main_port}\n".encode("windows-1251"))
        await writer.drain()
        writer.close()
    except:
        pass
    finally:
        writer.close()
        await writer.wait_closed()

async def main():
    """Главная функция сервера"""
    server = await asyncio.start_server(handle_client, host, port)
    
    async with server:
       await server.serve_forever()
