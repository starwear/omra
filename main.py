# -*- coding: utf-8 -*-

# OMRA by Starwear

# Импортируем библиотеки
import asyncio, mrim.main_server, mrim.redirect_server, os, logging
from dotenv import load_dotenv

# Загрузка конфигурации сервера
load_dotenv()

telegram_bot_token = os.environ.get("telegram_bot_token")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Словарь клиентов
clients = {}

# Словарь статусов
presences = {}

async def main():
    await asyncio.gather(
        mrim.redirect_server.main(),
        mrim.main_server.main()
    )

if __name__ == "__main__":
    asyncio.run(
        main()
    )