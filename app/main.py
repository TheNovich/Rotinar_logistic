'''Импорт библиотеки для работы с телеграм ботами pyTelegramBotApi'''
import telebot
from telebot.types import Message
from telebot import types

'''Импорт библиотеки для работы с БД sql SupaBase'''
from supabase import create_client

# Конфигурация
url = 'https://desgxzdvmuwywlfguzpz.supabase.co'
key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRlc2d4emR2bXV3eXdsZmd1enB6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI5MzI3MzYsImV4cCI6MjA2ODUwODczNn0.1sDkrlI6efDch_JafV23bGjuGev55Pf5xUiecsEsDSU'
bot = telebot.TeleBot('8057997671:AAGXbnh8dF3nF_A8u709R4U-k2ayyDwocUs')
supabase = create_client(url, key)



# Проверка роли пользователя
'''def check_user_role(telegram_id):
    user = supabase.table('users').select('role').eq('telegram_id', telegram_id).execute()
    return user.data[0]['role'] if user.data else None'''


'''# Декоратор для проверки ролей
def role_required(*allowed_roles):
    def decorator(func):
        def wrapper(message: Message, *args, **kwargs):
            user_role = check_user_role(message.from_user.id)
            if user_role not in allowed_roles:
                bot.reply_to(message, "⚠️ У вас недостаточно прав!")
                return
            return func(message, *args, **kwargs)

        return wrapper

    return decorator'''


# Обновленная функция регистрации
'''def process_phone(message):
    phone = message.text
    if not phone.isdigit() or len(phone) != 11:
        bot.send_message(message.chat.id, '❌ Неверный формат! Попробуйте ещё раз.')
        registration(message)
    elif search_number(phone) == 0:
        bot.send_message(message.chat.id, '❌ Номер не найден в системе!')
        registration(message)
    else:
        update_data_tg_id('users', {
            'telegram_id': message.from_user.id,
            'telegram_name': message.from_user.username
        }, phone)
        role = check_user_role(message.chat.id)
        bot.send_message(message.chat.id, f'✅ Вы успешно зарегистрированы! Роль: {role}')
        user_verification(message)'''


# Команда для изменения роли (только для админов)
'''@bot.message_handler(commands=['set_role'])
@role_required('admin')
def set_role(message):
    try:
        _, phone, new_role = message.text.split()
        if search_number(phone) == 0:
            bot.reply_to(message, "❌ Пользователь с таким номером не найден!")
            return

        supabase.table('users').update({'role': new_role}).eq('phone_number', phone).execute()
        bot.reply_to(message, f"✅ Роль обновлена! Пользователь {phone} теперь {new_role}")
    except:
        bot.reply_to(message, "❌ Использование: /set_role [phone] [role]")'''

'''def on_click_driver_panel(message):
    if message.text == 'Взять заказ':
        driver_next_status(message, 1, 'Заказ успешно взят в работу! \nНаправляйтесь к клиенту')
    elif message.text == 'Начать смену':
        start_driver_shift(message)
    elif message.text == 'Завершить смену':
        finish_driver_shift(message)
    elif message.text == 'Перейти к этапу загрузки автомобиля':
        driver_next_status(message, 2, 'Вы находитесь на месте загрузки автомобиля. \nПосле загрузки смените ваш статус на "Выдвинуться на точку разгрузки"')
    elif message.text == 'Выдвинуться на точку разгрузки':
        driver_next_status(message, 3, 'Вы находитесь на месте загрузки автомобиля. \nПосле загрузки смените ваш статус на "Выдвинуться на точку разгрузки"')
    elif message.text == 'Разгрузка автомобиля':
        driver_next_status(message, 4, 'Вы находитесь на месте разгрузки автомобилья. \nПосле прибытия смените ваш статус на "Завершить заказ"')
    elif message.text == 'Завершить заказ':
        driver_next_status(message, 5, 'Вы успешно завершили заказ. \nОжидайте поступления нового заказа')

    driver_panel(message)

def driver_next_status(message, next_status_id, message_to_user):
    supabase.table('users').update('state_id', next_status_id).eq('telegram_id', message.from_user.id).execute()
    bot.reply_to(message, message_to_user)'''

'''def driver_complete_order(message):
    supabase.table('users').update({'state_id': 5}).eq('telegram_id', message.from_user.id).execute()
    bot.reply_to(message,'Вы успешно завершили заказ. \nОжидайте поступления нового заказа')'''

'''def driver_unloading_car(message):
    supabase.table('users').update({'state_id': 4}).eq('telegram_id', message.from_user.id).execute()
    bot.reply_to(message,'Вы находитесь на месте разгрузки автомобилья. \nПосле прибытия смените ваш статус на "Завершить заказ"')'''
'''def driver_way_unloading(message):
    supabase.table('users').update({'state_id': 3}).eq('telegram_id', message.from_user.id).execute()
    bot.reply_to(message,'Вы выдвинулись на точку разгрузки. \nПосле прибытия смените ваш статус на "Разгрузка автомобиля"')'''
'''def driver_loading_cat_state(message):
    supabase.table('users').update({'state_id': 2}).eq('telegram_id', message.from_user.id).execute()
    bot.reply_to(message, 'Вы находитесь на месте загрузки автомобиля. \nПосле загрузки смените ваш статус на "Выдвинуться на точку разгрузки"')'''
'''def driver_take_order(message):
    supabase.table('users').update({'state_id': 1}).eq('telegram_id', message.from_user.id).execute()
    bot.send_message(message.chat.id, 'Заказ успешно взят в работу! \n Направляйтесь к клиенту')'''

'''def convert_to_string(array):
    i = 0
    list = ''
    for i in range(array.len):
        list += 'f{}' '''

'''def on_click_manager_panel(message):
    if message.text == 'Свободные водители':
        free_drivers = supabase.table('users') \
            .select('last_name', 'first_name', 'surname', 'phone_number') \
            .or_('and(role.eq.driver, state_id.eq.5)') \
            .execute()

        # Форматируем данные водителей
        drivers_list = []
        for driver in free_drivers.data:
            # Собираем информацию о каждом водителе
            driver_info = (
                f"Фамилия: {driver['last_name']}\n"
                f"Имя: {driver['first_name']}\n"
                f"Отчество: {driver['surname']}\n"
                f"Телефон: {driver['phone_number']}\n"
                "-------------------------"
            )
            drivers_list.append(driver_info)

        # Объединяем всех водителей в одно сообщение
        if drivers_list:
            response = "Свободные водители:\n\n" + "\n".join(drivers_list)
        else:
            response = "Свободных водителей нет"

        # Отправляем сообщение
        bot.reply_to(message, response)
    else: bot.reply_to(message, '❌ Неверная команда')
    manager_panel(message)'''

'''@bot.message_handler(commands=['manager_panel'])
@role_required('manager', 'admin')
def manager_panel(message):
    markup = types.ReplyKeyboardMarkup()
    free_drivers_button = types.KeyboardButton('Свободные водители')
    markup.row(free_drivers_button)
    bot.send_message(message.chat.id, 'Выберите действие', reply_markup=markup)
    bot.register_next_step_handler(message, on_click_manager_panel)'''


'''@bot.message_handler(commands=['driver_panel'])
@role_required('driver', 'admin')
def driver_panel(message):
    markup = types.ReplyKeyboardMarkup()
    is_on_shift = supabase.table('users').select('is_on_shift').eq('telegram_id', message.from_user.id).execute()
    driver_state = supabase.table('users').select('state_id').eq('telegram_id', message.from_user.id).execute()
    if is_on_shift.data[0]['is_on_shift'] == True:
        driver_finish_button = types.KeyboardButton('Завершить смену')
        markup.row(driver_finish_button)
    else:
        driver_start_button = types.KeyboardButton('Начать смену')
        markup.row(driver_start_button)
    if driver_state.data[0]['state_id'] == 1:
        driver_loading_car_button = types.KeyboardButton('Перейти к этапу загрузки автомобиля')
        markup.row(driver_loading_car_button)
    elif driver_state.data[0]['state_id'] == 2:
        driver_loading_car_button = types.KeyboardButton('Выдвинуться на точку разгрузки')
        markup.row(driver_loading_car_button)
    elif driver_state.data[0]['state_id'] == 3:
        driver_loading_car_button = types.KeyboardButton('Разгрузка автомобиля')
        markup.row(driver_loading_car_button)
    elif driver_state.data[0]['state_id'] == 4:
        driver_loading_car_button = types.KeyboardButton('Завершить заказ')
        markup.row(driver_loading_car_button)
    elif driver_state.data[0]['state_id'] == 5:
        driver_take_order_button = types.KeyboardButton('Взять заказ')
        markup.row(driver_take_order_button)

    bot.send_message(message.chat.id, 'Выберите действие', reply_markup=markup)
    bot.register_next_step_handler(message, on_click_driver_panel)'''


'''def start_driver_shift(message):
    tg_id = message.from_user.id
    supabase.table('users').update({'is_on_shift': True}).eq('telegram_id', tg_id).execute()
    bot.send_message(message.chat.id, 'Вы на смене!')'''

'''def finish_driver_shift(message):
    tg_id = message.from_user.id
    supabase.table('users').update({'is_on_shift': False}).eq('telegram_id', tg_id).execute()
    bot.send_message(message.chat.id, 'Смена завершена!')'''

# Остальные ваши функции без изменений
'''def update_data_tg_id(table, data, phone):
    supabase.table(table).update(data).eq('phone_number', phone).execute()


def search_number(phone):
    response = supabase.table('users').select('phone_number', count='exact').eq('phone_number', phone).execute()
    return response.count'''


'''def registration(message):
    msg = bot.send_message(message.chat.id,
                           'Введите номер телефона в формате 89991112233 (без пробелов и спецсимволов):')
    bot.register_next_step_handler(msg, process_phone)'''


'''@bot.message_handler(commands=['start'])
def user_verification(message):
    response = supabase.table('users').select('telegram_id', count='exact').eq('telegram_id', message.chat.id).execute()
    if response.count != 0:
        role = check_user_role(message.chat.id)
        bot.send_message(message.chat.id, f'✅ Вы авторизованы! Ваша роль: {role}')
        role_commands(message, role)
    else:
        registration(message)'''

'''def role_commands(message, role):
    if role == 'driver':
        driver_panel(message)
    elif role == 'manager':
        manager_panel(message)'''

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
                timeout=60,
                long_polling_timeout=30
            )
        except RequestsConnectionError as e:
            logging.error(f"Network error: {e}")
            logging.info(f"Restarting in {restart_delay} seconds...")
            time.sleep(restart_delay)

            # Экспоненциальное увеличение задержки
            restart_delay = min(restart_delay * 2, 60)  # Макс. 60 секунд

        except Exception as e:
            logging.exception(f"Critical error: {e}")
            logging.info("Restarting in 10 seconds...")
            time.sleep(10)
            restart_delay = 5  # Сброс задержки


if __name__ == '__main__':
    # Ваша инициализация бота и обработчиков

    # Запускаем устойчивый polling
    robust_polling()