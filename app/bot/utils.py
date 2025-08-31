import time
from requests.exceptions import ConnectionError, ReadTimeout
from telebot.apihelper import ApiException

'импорт библиотеки pyTelegramBotApi'
from telebot.types import Message
from telebot import types
from telebot.handler_backends import State, StatesGroup
from app.bot.order_creation import create_order


'from handlers import manager_panel'

'Импорт функций взаимодействия с ДБ'
from app.database.crud import check_user_role, search_number, update_data_tg_id, switch_driver_status, switch_driver_shift, supabase
'from app.bot.handlers import driver_panel, manager_panel'

from app.bot.instance import bot


def safe_send_message(chat_id, text, max_retries=3, retry_delay=2, **kwargs):
    """
    Безопасная отправка сообщения с обработкой ошибок и повторными попытками
    Поддерживает ВСЕ аргументы оригинального send_message:
    - reply_markup
    - parse_mode
    - disable_web_page_preview
    - reply_to_message_id
    - и любые другие параметры

    Параметры:
        chat_id: ID чата
        text: Текст сообщения
        max_retries: Максимальное количество попыток
        retry_delay: Базовая задержка между попытками (сек)
        **kwargs: Любые дополнительные параметры для send_message
    """
    for attempt in range(max_retries):
        try:
            return bot.send_message(chat_id, text, **kwargs)

        except (ConnectionResetError, ApiException) as e:
            # Логируем ошибку
            print(f"Ошибка отправки (попытка {attempt + 1}/{max_retries}): {type(e).__name__} - {e}")

            # Экспоненциальная backoff-задержка
            delay = retry_delay * (2 ** attempt)
            time.sleep(delay)

        except Exception as e:
            # Обработка непредвиденных ошибок
            print(f"Критическая ошибка при отправке: {type(e).__name__} - {e}")
            raise  # Пробрасываем выше для обработки в основном коде

    # Если все попытки исчерпаны
    print(f"⚠️ Не удалось отправить сообщение после {max_retries} попыток")
    return None

# Функция сохранения заказа (заглушка)
def save_order_to_db(order_data):
    """Сохраняет заказ в базе данных и возвращает ID созданного заказа"""
    # Здесь должна быть реальная логика сохранения
    import random
    return random.randint(1000, 9999)

'Декоратор для проверки ролей'
def role_required(*allowed_roles):
    def decorator(func):
        def wrapper(message: Message, *args, **kwargs):
            user_role = check_user_role(message.from_user.id)
            if user_role not in allowed_roles:
                safe_send_message(message.chat.id, "⚠️ У вас недостаточно прав!")
                return
            return func(message, *args, **kwargs)

        return wrapper

    return decorator

'Функция регистрации проверяет валидирует формат введённого номера телефона и проверяет есть ли он в бд'
def process_phone(message, driver_panel, manager_panel):
    phone = message.text
    if not phone.isdigit() or len(phone) != 11:
        safe_send_message(message.chat.id, '❌ Неверный формат! Попробуйте ещё раз.')
        registration(message, driver_panel, manager_panel)
    elif search_number(phone) == 0:
        safe_send_message(message.chat.id, '❌ Номер не найден в системе!')
        registration(message, driver_panel, manager_panel)
    else:
        update_data_tg_id('users', {
            'telegram_id': message.from_user.id,
            'telegram_name': message.from_user.username
        }, phone)
        user_verification(message, driver_panel, manager_panel)


def on_click_driver_panel(message, driver_panel):
    if message.text == 'Начать смену 🚀':
        start_driver_shift(message)
    elif message.text == 'Завершить смену 🏁':
        finish_driver_shift(message)
    elif message.text == 'Взять заказ':
        driver_next_status(message, 1, 'Заказ успешно взят в работу! \nНаправляйтесь к клиенту')
    elif message.text == 'Перейти к этапу загрузки автомобиля':
        driver_next_status(message, 2, 'Вы находитесь на месте загрузки автомобиля. \nПосле загрузки смените ваш статус на "Выдвинуться на точку разгрузки"')
    elif message.text == 'Выдвинуться на точку разгрузки':
        driver_next_status(message, 3, 'Вы находитесь на пути в точку разгрузки автомобиля. \nПосле прибытия смените ваш статус на "Разгрузка автомобиля"')
    elif message.text == 'Разгрузка автомобиля':
        driver_next_status(message, 4, 'Вы находитесь на месте разгрузки автомобилья. \nПосле прибытия смените ваш статус на "Завершить заказ"')
    elif message.text == 'Завершить заказ':
        driver_next_status(message, 5, 'Вы успешно завершили заказ. \nОжидайте поступления нового заказа')
    elif message.text == 'Отменить заказ ❌':
        driver_next_status(message,5, 'Заказ отменён, ваш статус "Свободен"')
    elif message.text == 'Перерыв ⏸️':
        driver_next_status(message, 6, 'Вы находитесь на перерыве')
    elif message.text == 'Завершить перерыв ▶️':
        driver_next_status(message, 5, 'Перерыв завершён, ваш статус "Свободен"')


    driver_panel(message)

def driver_next_status(message, next_status_id, message_to_user):
    switch_driver_status(next_status_id, message.from_user.id)
    safe_send_message(message.chat.id, message_to_user)

def start_driver_shift(message):
    tg_id = message.from_user.id
    switch_driver_shift(True, tg_id)
    switch_driver_status(5, tg_id)
    safe_send_message(message.chat.id, 'Вы на смене!')

def finish_driver_shift(message):
    tg_id = message.from_user.id
    switch_driver_shift(False, tg_id)
    switch_driver_status(5, tg_id)
    safe_send_message(tg_id, 'Смена завершена!')

def registration(message, driver_panel, manager_panel):
    msg = safe_send_message(message.chat.id,
                           'Введите номер телефона в формате 89991112233 (без пробелов и спецсимволов):')
    bot.register_next_step_handler(msg, lambda msg: process_phone(msg, driver_panel, manager_panel))

def role_commands(message, role, driver_panel, manager_panel):
    if role == 'driver':
        driver_panel(message)
    elif role == 'manager':
        manager_panel(message)


def on_click_manager_panel(message, manager_panel):
    def convert_to_international(phone):
        """Преобразует российский номер 8... в международный формат +7..."""
        if phone.startswith('8') and len(phone) == 11:
            return '+7' + phone[1:]
        return phone

    if message.text == 'Свободные водители':
        free_drivers = supabase.table('users') \
            .select('last_name', 'first_name', 'surname', 'phone_number', 'state_id') \
            .eq('role', 'driver') \
            .eq('state_id', 5) \
            .eq('is_on_shift', True) \
            .execute()

        drivers_list = []
        for driver in free_drivers.data:
            # Конвертируем номер в международный формат
            international_phone = convert_to_international(driver['phone_number'])
            phone_link = f"<a href='tel:{international_phone}'>{international_phone}</a>"

            driver_info = (
                f"{driver['last_name']} "
                f"{driver['first_name']} "
                f"{driver['surname']}\n"
                f"{phone_link}\n"
                f"Свободен✅\n"
                "-------------------------"
            )
            drivers_list.append(driver_info)

        if drivers_list:
            response = "Свободные водители:\n\n" + "\n".join(drivers_list)
        else:
            response = "Свободных водителей нет"

        safe_send_message(message.chat.id, response, parse_mode='HTML')
        manager_panel(message)

    elif message.text == 'Все водители':
        all_drivers = supabase.table('users') \
            .select('last_name', 'first_name', 'surname', 'phone_number', 'state_id') \
            .eq('role', 'driver') \
            .eq('is_on_shift', True) \
            .in_('state_id', [1, 2, 3, 4, 5, 6]) \
            .execute()

        status_names = {
            1: "Выдвинулся на погрузку 🚘",
            2: "Погрузка автомобиля 🪝",
            3: "Едет на выгрузку 🚨",
            4: "Выгрузка автомобиля 🔄",
            5: "Свободен ✅",
            6: "Перерыв ⏸️"
        }

        drivers_list = []
        for driver in all_drivers.data:
            # Конвертируем номер в международный формат
            international_phone = convert_to_international(driver['phone_number'])
            phone_link = f"<a href='tel:{international_phone}'>{international_phone}</a>"
            status = status_names.get(driver['state_id'], "Неизвестный статус")

            driver_info = (
                f"{driver['last_name']} "
                f"{driver['first_name']} "
                f"{driver['surname']}\n"
                f"{phone_link}\n"
                f"{status}\n"
                "-------------------------"
            )
            drivers_list.append(driver_info)

        if drivers_list:
            response = "Все водители:\n\n" + "\n".join(drivers_list)
        else:
            response = "Водителей не найдено"

        safe_send_message(message.chat.id, response, parse_mode='HTML')
        manager_panel(message)

    elif message.text == '📝 Создать заказ':
        create_order(message, manager_panel)

    else:
        safe_send_message(message.chat.id, '❌ Неверная команда')
        manager_panel(message)

def user_verification(message, driver_panel, manager_panel):
    response = supabase.table('users').select('telegram_id', count='exact').eq('telegram_id', message.chat.id).execute()
    if response.count != 0:
        role = check_user_role(message.chat.id)
        safe_send_message(message.chat.id, f'✅ Вы авторизованы! Ваша роль: {role}')
        role_commands(message, role, driver_panel, manager_panel)
    else:
        registration(message, driver_panel, manager_panel)

def convert_to_international(phone):
    """Преобразует российский номер 8... в международный формат +7..."""
    if phone.startswith('8') and len(phone) == 11:
        return '+7' + phone[1:]
    return phone  # Если уже в международном формате или другой стране