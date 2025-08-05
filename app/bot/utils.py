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
                bot.reply_to(message, "⚠️ У вас недостаточно прав!")
                return
            return func(message, *args, **kwargs)

        return wrapper

    return decorator

'Функция регистрации проверяет валидирует формат введённого номера телефона и проверяет есть ли он в бд'
def process_phone(message, driver_panel, manager_panel):
    phone = message.text
    if not phone.isdigit() or len(phone) != 11:
        bot.send_message(message.chat.id, '❌ Неверный формат! Попробуйте ещё раз.')
        registration(message, driver_panel, manager_panel)
    elif search_number(phone) == 0:
        bot.send_message(message.chat.id, '❌ Номер не найден в системе!')
        registration(message, driver_panel, manager_panel)
    else:
        update_data_tg_id('users', {
            'telegram_id': message.from_user.id,
            'telegram_name': message.from_user.username
        }, phone)
        role = check_user_role(message.chat.id)
        '''bot.send_message(message.chat.id, f'✅ Вы успешно зарегистрированы! Роль: {role}')'''
        user_verification(message, driver_panel, manager_panel)


def on_click_driver_panel(message, driver_panel):
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
    switch_driver_status(next_status_id, message.from_user.id)
    bot.reply_to(message, message_to_user)

def start_driver_shift(message):
    tg_id = message.from_user.id
    switch_driver_shift(True, tg_id)
    bot.send_message(message.chat.id, 'Вы на смене!')

def finish_driver_shift(message):
    tg_id = message.from_user.id
    switch_driver_shift(False, tg_id)
    bot.send_message(message.chat.id, 'Смена завершена!')

def registration(message, driver_panel, manager_panel):
    msg = bot.send_message(message.chat.id,
                           'Введите номер телефона в формате 89991112233 (без пробелов и спецсимволов):')
    bot.register_next_step_handler(msg, lambda msg: process_phone(msg, driver_panel, manager_panel))

def role_commands(message, role, driver_panel, manager_panel):
    if role == 'driver':
        driver_panel(message)
    elif role == 'manager':
        manager_panel(message)

def on_click_manager_panel(message, manager_panel):
    if message.text == 'Свободные водители':
        free_drivers = supabase.table('users') \
            .select('last_name', 'first_name', 'surname', 'phone_number') \
            .or_('and(role.eq.driver, state_id.eq.5)') \
            .execute()

        # Форматируем данные водителей
        drivers_list = []
        for driver in free_drivers.data:
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
        manager_panel(message)  # Показываем панель снова после выполнения

    elif message.text == '📝 Создать заказ':
        # Запускаем процесс создания заказа
        create_order(message, manager_panel)
        # Не вызываем manager_panel здесь - FSM будет управлять диалогом

    else:
        bot.reply_to(message, '❌ Неверная команда')
        manager_panel(message)  # Показываем панель снова при ошибке

def user_verification(message, driver_panel, manager_panel):
    response = supabase.table('users').select('telegram_id', count='exact').eq('telegram_id', message.chat.id).execute()
    if response.count != 0:
        role = check_user_role(message.chat.id)
        bot.send_message(message.chat.id, f'✅ Вы авторизованы! Ваша роль: {role}')
        role_commands(message, role, driver_panel, manager_panel)
    else:
        registration(message, driver_panel, manager_panel)