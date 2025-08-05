# order_creation.py
from telebot import types
from app.bot.instance import bot

# Глобальный словарь для временных данных
temp_orders = {}

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


