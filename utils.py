# -*- coding: utf-8 -*-

# OMRA by Starwear

# Импортирование библиотек
import logging, os
from dotenv import load_dotenv

# Загрузка конфигурации сервера
load_dotenv()

# Токен телеграм бота для SMS
telegram_bot_token = os.environ.get("telegram_bot_token")

# Словарь клиентов
clients = {}

# Словарь статусов
presences = {}

# Логер
logger = logging.getLogger("omra_server")
logging.basicConfig(level=logging.INFO)
