'импорт библиотеки pyTelegramBotApi'
from telebot.types import Message
from telebot import types
from telebot.handler_backends import State, StatesGroup
'from handlers import manager_panel'

'Импорт функций взаимодействия с ДБ'
from app.database.crud import check_user_role, search_number, update_data_tg_id, switch_driver_status, switch_driver_shift, supabase
'from app.bot.handlers import driver_panel, manager_panel'

from app.bot.instance import bot

class OrderStates(StatesGroup):
    address_from = State()
    address_to = State()
    car_model = State()
    phone = State()
    price = State()
    client_name = State()
    extra_services = State()
    comment = State()

# Обработчик отмены заказа
def cancel_order(message, manager_panel):
    bot.delete_state(message.from_user.id, message.chat.id)
    bot.send_message(message.chat.id, "❌ Создание заказа отменено")
    manager_panel(message)  # Возвращаем в менеджерскую панель

# Обработчики для каждого состояния (address_from, address_to, и т.д.)
# Используйте код из предыдущего ответа, начиная с @bot.message_handler(state=OrderStates.address_from)
# Не забудьте добавить вызов manager_panel после завершения/отмены заказа


def create_order(message, manager_panel):
    # Инициализация структуры для хранения данных заказа
    order_data = {}

    # Запрос первого параметра
    msg = bot.send_message(
        message.chat.id,
        "🚚 *Шаг 1/8: Введите адрес подачи эвакуатора*\n"
        "Пример: _Москва, Ленинский проспект, 42_",
        parse_mode="Markdown",
        reply_markup=cancel_markup()
    )

    # Регистрация следующего шага
    bot.register_next_step_handler(msg, lambda msg: process_address_from(msg, order_data, manager_panel))


def process_address_from(message, order_data, manager_panel):
    # Проверка на отмену
    if message.text == "❌ Отменить создание заказа":
        cancel_order(message)
        return

    # Валидация
    if len(message.text) < 5:
        msg = bot.send_message(message.chat.id, "⚠️ Адрес слишком короткий! Введите полный адрес:")
        bot.register_next_step_handler(msg, lambda msg: process_address_from(msg, order_data, manager_panel))
        return

    order_data['address_from'] = message.text

    # Запрос следующего параметра
    msg = bot.send_message(
        message.chat.id,
        "🏁 *Шаг 2/8: Введите адрес назначения*\n"
        "Пример: _Санкт-Петербург, Невский проспект, 15_",
        parse_mode="Markdown",
        reply_markup=cancel_markup()
    )
    bot.register_next_step_handler(msg, lambda msg: process_address_to(msg, order_data, manager_panel))


def process_address_to(message, order_data, manager_panel):
    if message.text == "❌ Отменить создание заказа":
        cancel_order(message)
        return

    if len(message.text) < 5:
        msg = bot.send_message(message.chat.id, "⚠️ Адрес слишком короткий! Введите полный адрес:")
        bot.register_next_step_handler(msg, lambda msg: process_address_to(msg, order_data, manager_panel))
        return

    order_data['address_to'] = message.text

    # Запрос следующего параметра
    msg = bot.send_message(
        message.chat.id,
        "🚗 *Шаг 3/8: Введите марку и модель автомобиля*\n"
        "Пример: _Toyota Camry 2020 года_",
        parse_mode="Markdown",
        reply_markup=cancel_markup()
    )
    bot.register_next_step_handler(msg, lambda msg: process_car_model(msg, order_data, manager_panel))


def process_car_model(message, order_data, manager_panel):
    if message.text == "❌ Отменить создание заказа":
        cancel_order(message)
        return

    order_data['car_model'] = message.text

    # Запрос следующего параметра
    msg = bot.send_message(
        message.chat.id,
        "📱 *Шаг 4/8: Введите номер телефона клиента*\n"
        "Формат: _89161234567_",
        parse_mode="Markdown",
        reply_markup=cancel_markup()
    )
    bot.register_next_step_handler(msg,  lambda msg: process_client_phone(msg, order_data, manager_panel))


def process_client_phone(message, order_data, manager_panel):
    if message.text == "❌ Отменить создание заказа":
        cancel_order(message)
        return

    phone = message.text.strip()
    if not (phone[1:].isdigit() and len(phone) >= 11):
        msg = bot.send_message(
            message.chat.id,
            "⚠️ Неверный формат номера! Пожалуйста, используйте формат:\n"
            "_89161234567_",
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(msg, lambda msg: process_client_phone(msg, order_data, manager_panel))
        return

    order_data['phone'] = phone

    # Запрос следующего параметра
    msg = bot.send_message(
        message.chat.id,
        "💵 *Шаг 5/8: Введите стоимость услуги*\n"
        "Пример: _3500_",
        parse_mode="Markdown",
        reply_markup=cancel_markup()
    )
    bot.register_next_step_handler(msg,  lambda msg: process_price(msg, order_data, manager_panel))


def process_price(message, order_data, manager_panel):
    if message.text == "❌ Отменить создание заказа":
        cancel_order(message)
        return

    try:
        price = float(message.text.replace(',', '.'))
        if price <= 0:
            raise ValueError
    except ValueError:
        msg = bot.send_message(message.chat.id, "⚠️ Неверная сумма! Введите число (например: 3500):")
        bot.register_next_step_handler(msg, lambda msg: process_price(msg, order_data, manager_panel))
        return

    order_data['price'] = price

    # Запрос необязательного параметра
    msg = bot.send_message(
        message.chat.id,
        "👤 *Шаг 6/8: Введите ФИО клиента (необязательно)*",
        parse_mode="Markdown",
        reply_markup=skip_markup()
    )
    bot.register_next_step_handler(msg, lambda msg: process_client_name(msg, order_data, manager_panel))


def process_client_name(message, order_data, manager_panel):
    if message.text == "❌ Отменить создание заказа":
        cancel_order(message)
        return

    if message.text == "⏭ Пропустить":
        order_data['client_name'] = "Не указано"
    else:
        order_data['client_name'] = message.text

    # Запрос следующего необязательного параметра
    msg = bot.send_message(
        message.chat.id,
        "🔧 *Шаг 7/8: Дополнительные услуги (необязательно)*\n"
        "Пример: _Мойка, доставка ключей, хранение авто_",
        parse_mode="Markdown",
        reply_markup=skip_markup()
    )
    bot.register_next_step_handler(msg, lambda msg: process_extra_services(msg, order_data, manager_panel))


def process_extra_services(message, order_data, manager_panel):
    if message.text == "❌ Отменить создание заказа":
        cancel_order(message)
        return

    if message.text == "⏭ Пропустить":
        order_data['extra_services'] = "Нет"
    else:
        order_data['extra_services'] = message.text

    # Запрос последнего параметра
    msg = bot.send_message(
        message.chat.id,
        "📝 *Шаг 8/8: Комментарий к заказу (необязательно)*",
        parse_mode="Markdown",
        reply_markup=skip_markup()
    )
    bot.register_next_step_handler(msg, lambda msg: process_comment(msg, order_data, manager_panel))


def process_comment(message, order_data, manager_panel):
    if message.text == "❌ Отменить создание заказа":
        cancel_order(message, manager_panel)
        return

    if message.text == "⏭ Пропустить":
        order_data['comment'] = "Нет"
    else:
        order_data['comment'] = message.text

    # Формируем сводку заказа
    order_text = format_order(order_data)

    # Запрашиваем подтверждение
    confirm_markup = types.InlineKeyboardMarkup()
    confirm_markup.row(
        types.InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_order_{message.chat.id}"),
        types.InlineKeyboardButton("🔄 Перезаполнить", callback_data=f"restart_order_{message.chat.id}")
    )

    bot.send_message(
        message.chat.id,
        f"📋 *Детали заказа:*\n\n{order_text}\n\nПодтверждаете создание заказа?",
        parse_mode="Markdown",
        reply_markup=confirm_markup
    )

    # Сохраняем данные для подтверждения
    global temp_orders
    temp_orders[message.chat.id] = order_data


# Вспомогательные функции
def cancel_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("❌ Отменить создание заказа"))
    return markup


def skip_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("⏭ Пропустить"))
    markup.add(types.KeyboardButton("❌ Отменить создание заказа"))
    return markup


def format_order(data):
    return (
        f"🚚 *Откуда:* {data.get('address_from', '')}\n"
        f"🏁 *Куда:* {data.get('address_to', '')}\n"
        f"🚗 *Авто:* {data.get('car_model', '')}\n"
        f"📞 *Телефон:* {data.get('phone', '')}\n"
        f"💵 *Стоимость:* {data.get('price', '')} руб\n"
        f"👤 *Клиент:* {data.get('client_name', 'Не указано')}\n"
        f"🔧 *Доп.услуги:* {data.get('extra_services', 'Нет')}\n"
        f"📝 *Комментарий:* {data.get('comment', 'Нет')}"
    )


def cancel_order(message, manager_panel):
    bot.send_message(message.chat.id, "❌ Создание заказа отменено", reply_markup=types.ReplyKeyboardRemove())
    manager_panel(message)


# Глобальная переменная для временного хранения данных
temp_orders = {}





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