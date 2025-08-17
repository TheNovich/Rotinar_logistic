'''Импорт библиотеки для работы с телеграм ботами pyTelegramBotApi'''
import telebot
from telebot.types import Message
from telebot import types

import sys
import os

# Получаем путь к корню проекта (папка Rotinar)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

'''Импорт библиотеки для работы с БД sql SupaBase'''
from supabase import create_client
from config import config

# Конфигурация
url = config.SUPABASE_URL
key = config.SUPABASE_KEY
bot = telebot.TeleBot(config.TELEGRAM_TOKEN)
supabase = create_client(url, key)


import time
import logging
from requests.exceptions import ConnectionError as RequestsConnectionError

from app.bot.instance import bot
from app.bot.handlers import start_handler, driver_panel, manager_panel

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_errors.log'),
        logging.StreamHandler()
    ]
)


def robust_polling():
    """Устойчивый запуск бота с обработкой сетевых ошибок"""
    restart_delay = 5  # Начальная задержка перезапуска

    while True:
        try:
            logging.info("Starting bot polling...")
            bot.polling(
                none_stop=True,
                interval=2,
                timeout=5,
                long_polling_timeout=10
            )
        except RequestsConnectionError as e:
            logging.error(f"Network error: {e}")
            logging.info(f"Restarting in {restart_delay} seconds...")
            time.sleep(restart_delay)

            # Экспоненциальное увеличение задержки
            restart_delay = min(restart_delay * 10, 60)  # Макс. 60 секунд

        except Exception as e:
            logging.exception(f"Critical error: {e}")
            logging.info("Restarting in 10 seconds...")
            time.sleep(10)
            restart_delay = 5  # Сброс задержки


if __name__ == '__main__':
    # Ваша инициализация бота и обработчиков

    # Запускаем устойчивый polling
    robust_polling()