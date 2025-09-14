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

temp_new_users = {}
temp_delete_users = {}


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
def process_phone(message, driver_panel, manager_panel, admin_panel):
    phone = message.text
    if not phone.isdigit() or len(phone) != 11:
        safe_send_message(message.chat.id, '❌ Неверный формат! Попробуйте ещё раз.')
        registration(message, driver_panel, manager_panel, admin_panel)
    elif search_number(phone) == 0:
        safe_send_message(message.chat.id, '❌ Номер не найден в системе!')
        registration(message, driver_panel, manager_panel, admin_panel)
    else:
        update_data_tg_id('users', {
            'telegram_id': message.from_user.id,
            'telegram_name': message.from_user.username
        }, phone)
        user_verification(message, driver_panel, manager_panel, admin_panel)


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

def registration(message, driver_panel, manager_panel, admin_panel):
    msg = safe_send_message(message.chat.id,
                           'Введите номер телефона в формате 89991112233 (без пробелов и спецсимволов):')
    bot.register_next_step_handler(msg, lambda msg: process_phone(msg, driver_panel, manager_panel, admin_panel))

def role_commands(message, role, driver_panel, manager_panel, admin_panel):
    if role == 'driver':
        driver_panel(message)
    elif role == 'manager':
        manager_panel(message)
    elif role == 'admin':
        admin_panel(message)


def on_click_manager_panel(message, manager_panel, admin_panel):
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

    elif message.text == 'Панель администратора':
        admin_panel(message)
        return

    else:
        safe_send_message(message.chat.id, '❌ Неверная команда')
        manager_panel(message)

def on_click_admin_panel(message, admin_panel, manager_panel):
    message_text = message.text
    if message_text == 'Добавить нового пользователя':
        create_new_user(message)
    elif message_text == 'Удалить пользователя':
        delete_user(message)
    elif message_text == 'Панель менеджера':
        manager_panel(message)
        return
    else:
        admin_panel(message)


def create_new_user(message):
    chat_id = message.chat.id
    temp_new_users[chat_id] = {'step': 'fio'}

    # Очищаем клавиатуру
    safe_send_message(chat_id, 'Введите ФИО нового пользователя\nНапример: "Иванов Иван Иванович"',
                      reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, process_new_user_fio)


def process_new_user_fio(message):
    chat_id = message.chat.id
    fio = message.text.strip()

    # Валидация ФИО (должно содержать хотя бы 2 слова)
    fio_parts = fio.split()
    if len(fio_parts) < 2:
        safe_send_message(chat_id, '❌ Неверный формат ФИО! Введите хотя бы фамилию и имя через пробел.',
                          reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, process_new_user_fio)
        return

    temp_new_users[chat_id]['fio'] = fio
    temp_new_users[chat_id]['step'] = 'phone'
    safe_send_message(chat_id, 'Введите номер телефона пользователя в формате "89998887766"',
                      reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, process_new_user_phone)


def process_new_user_phone(message):
    chat_id = message.chat.id
    phone = message.text.strip()

    # Валидация номера телефона
    if not phone.isdigit() or len(phone) != 11 or not phone.startswith('8'):
        safe_send_message(chat_id, '❌ Неверный формат номера! Введите 11 цифр, начиная с 8.',
                          reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, process_new_user_phone)
        return

    # Проверка на существующего пользователя
    if search_number(phone) > 0:
        safe_send_message(chat_id, '❌ Пользователь с таким номером уже существует!',
                          reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, process_new_user_phone)
        return

    temp_new_users[chat_id]['phone'] = phone
    temp_new_users[chat_id]['step'] = 'role'

    # Создаем клавиатуру с выбором роли
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton('менеджер'))
    markup.add(types.KeyboardButton('водитель'))
    markup.add(types.KeyboardButton('администратор'))

    safe_send_message(chat_id, 'Выберите роль пользователя:', reply_markup=markup)
    bot.register_next_step_handler(message, process_new_user_role)


def process_new_user_role(message):
    chat_id = message.chat.id
    role_text = message.text.strip().lower()

    # Валидация роли
    if role_text not in ['менеджер', 'водитель', 'администратор']:
        safe_send_message(chat_id, '❌ Неверная роль! Выберите из предложенных вариантов.')
        # Повторно показываем клавиатуру с ролями
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(types.KeyboardButton('менеджер'))
        markup.add(types.KeyboardButton('водитель'))
        markup.add(types.KeyboardButton('администратор'))
        safe_send_message(chat_id, 'Выберите роль пользователя:', reply_markup=markup)
        bot.register_next_step_handler(message, process_new_user_role)
        return

    # Преобразуем русские названия ролей в английские
    role_map = {
        'менеджер': 'manager',
        'водитель': 'driver',
        'администратор': 'admin'
    }
    role = role_map[role_text]

    temp_new_users[chat_id]['role'] = role
    temp_new_users[chat_id]['role_text'] = role_text

    # Показываем подтверждение с данными
    show_confirmation(chat_id, message)


def show_confirmation(chat_id, message):
    user_data = temp_new_users.get(chat_id, {})
    fio = user_data.get('fio', '')
    phone = user_data.get('phone', '')
    role_text = user_data.get('role_text', '')

    # Создаем клавиатуру с кнопками подтверждения
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton('Подтвердить'), types.KeyboardButton('Отредактировать'))
    markup.row(types.KeyboardButton('Отменить добавление'))

    # Отправляем сообщение с подтверждением и клавиатурой
    confirmation_message = (
        f"Проверьте введенные данные:\n\n"
        f"ФИО: {fio}\n"
        f"Номер телефона: {phone}\n"
        f"Роль: {role_text}"
    )

    safe_send_message(chat_id, confirmation_message, reply_markup=markup)
    bot.register_next_step_handler(message, handle_confirmation)


def handle_confirmation(message):
    chat_id = message.chat.id
    choice = message.text.strip()

    if choice == 'Подтвердить':
        # Получаем сохраненные данные
        user_data = temp_new_users.get(chat_id, {})
        fio = user_data.get('fio', '')
        phone = user_data.get('phone', '')
        role = user_data.get('role', '')

        # Разбиваем ФИО на составляющие
        fio_parts = fio.split()
        last_name = fio_parts[0]
        first_name = fio_parts[1] if len(fio_parts) > 1 else ''
        surname = fio_parts[2] if len(fio_parts) > 2 else ''

        try:
            # Создаем пользователя в БД
            from app.database.crud import create_user
            create_user(phone, first_name, last_name, surname, role)
            safe_send_message(chat_id, f'✅ Пользователь {fio} успешно добавлен!',
                              reply_markup=types.ReplyKeyboardRemove())
        except Exception as e:
            safe_send_message(chat_id, f'❌ Ошибка при добавлении пользователя: {str(e)}\nПопробуйте снова.',
                              reply_markup=types.ReplyKeyboardRemove())
            # Очищаем временные данные и начинаем заново
            if chat_id in temp_new_users:
                del temp_new_users[chat_id]
            create_new_user(message)
            return

        # Очищаем временные данные
        if chat_id in temp_new_users:
            del temp_new_users[chat_id]

        # Возвращаемся в админ-панель
        from app.bot.handlers import admin_panel
        admin_panel(message)

    elif choice == 'Отредактировать':
        # Предлагаем выбрать, что редактировать
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(types.KeyboardButton('ФИО'))
        markup.row(types.KeyboardButton('Номер телефона'))
        markup.row(types.KeyboardButton('Роль'))
        markup.row(types.KeyboardButton('Отменить редактирование'))

        safe_send_message(chat_id, 'Что вы хотите отредактировать?', reply_markup=markup)
        bot.register_next_step_handler(message, handle_edit_choice)

    elif choice == 'Отменить добавление':
        # Очищаем временные данные
        if chat_id in temp_new_users:
            del temp_new_users[chat_id]

        safe_send_message(chat_id, '❌ Добавление пользователя отменено.',
                          reply_markup=types.ReplyKeyboardRemove())

        # Возвращаемся в админ-панель
        from app.bot.handlers import admin_panel
        admin_panel(message)

    else:
        safe_send_message(chat_id, '❌ Неверный выбор. Пожалуйста, используйте кнопки.')
        show_confirmation(chat_id, message)


def handle_edit_choice(message):
    chat_id = message.chat.id
    choice = message.text.strip()

    if choice == 'ФИО':
        temp_new_users[chat_id]['step'] = 'fio'
        safe_send_message(chat_id, 'Введите новое ФИО:', reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, process_new_user_fio)

    elif choice == 'Номер телефона':
        temp_new_users[chat_id]['step'] = 'phone'
        safe_send_message(chat_id, 'Введите новый номер телефона:', reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, process_new_user_phone)

    elif choice == 'Роль':
        temp_new_users[chat_id]['step'] = 'role'
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(types.KeyboardButton('менеджер'))
        markup.add(types.KeyboardButton('водитель'))
        markup.add(types.KeyboardButton('администратор'))
        safe_send_message(chat_id, 'Выберите новую роль:', reply_markup=markup)
        bot.register_next_step_handler(message, process_new_user_role)

    elif choice == 'Отменить редактирование':
        show_confirmation(chat_id, message)

    else:
        safe_send_message(chat_id, '❌ Неверный выбор. Пожалуйста, используйте кнопки.')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(types.KeyboardButton('ФИО'))
        markup.row(types.KeyboardButton('Номер телефона'))
        markup.row(types.KeyboardButton('Роль'))
        markup.row(types.KeyboardButton('Отменить редактирование'))
        safe_send_message(chat_id, 'Что вы хотите отредактировать?', reply_markup=markup)
        bot.register_next_step_handler(message, handle_edit_choice)

def convert_to_international(phone):
    """Преобразует российский номер 8... в международный формат +7..."""
    if phone.startswith('8') and len(phone) == 11:
        return '+7' + phone[1:]
    return phone  # Если уже в международном формате или другой стране

def user_verification(message, driver_panel, manager_panel, admin_panel):
    response = supabase.table('users').select('telegram_id', count='exact').eq('telegram_id', message.chat.id).execute()
    if response.count != 0:
        role = check_user_role(message.chat.id)
        safe_send_message(message.chat.id, f'✅ Вы авторизованы! Ваша роль: {role}')
        role_commands(message, role, driver_panel, manager_panel, admin_panel)
    else:
        registration(message, driver_panel, manager_panel, admin_panel)


def delete_user(message):
    chat_id = message.chat.id
    temp_delete_users[chat_id] = {'step': 'phone'}

    # Очищаем клавиатуру и добавляем кнопку отмены
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('Отменить удаление пользователя'))

    safe_send_message(chat_id, 'Введите номер телефона пользователя для удаления в формате "89998887766":',
                      reply_markup=markup)
    bot.register_next_step_handler(message, process_delete_user_phone)


def process_delete_user_phone(message):
    chat_id = message.chat.id
    phone = message.text.strip()

    # Проверяем, не нажата ли кнопка отмены
    if phone == 'Отменить удаление пользователя':
        safe_send_message(chat_id, '❌ Удаление пользователя отменено.',
                          reply_markup=types.ReplyKeyboardRemove())
        # Возвращаемся в админ-панель
        from app.bot.handlers import admin_panel
        admin_panel(message)
        return

    # Валидация номера телефона
    if not phone.isdigit() or len(phone) != 11 or not phone.startswith('8'):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton('Отменить удаление пользователя'))
        safe_send_message(chat_id, '❌ Неверный формат номера! Введите 11 цифр, начиная с 8.', reply_markup=markup)
        bot.register_next_step_handler(message, process_delete_user_phone)
        return

    # Проверка на существующего пользователя
    if search_number(phone) == 0:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton('Отменить удаление пользователя'))
        safe_send_message(chat_id, '❌ Пользователь с таким номером не найден!', reply_markup=markup)
        bot.register_next_step_handler(message, process_delete_user_phone)
        return

    # Получаем информацию о пользователе
    user_info = supabase.table('users').select('*').eq('phone_number', phone).execute()
    if not user_info.data:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton('Отменить удаление пользователя'))
        safe_send_message(chat_id, '❌ Пользователь с таким номером не найден!', reply_markup=markup)
        bot.register_next_step_handler(message, process_delete_user_phone)
        return

    user_data = user_info.data[0]
    temp_delete_users[chat_id]['user_data'] = user_data
    temp_delete_users[chat_id]['step'] = 'confirmation'

    # Формируем информацию о пользователе
    fio = f"{user_data.get('last_name', '')} {user_data.get('first_name', '')} {user_data.get('surname', '')}"
    role = user_data.get('role', '')
    phone = user_data.get('phone_number', '')

    # Создаем клавиатуру с кнопками подтверждения
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton('Да, я абсолютно уверен'))
    markup.row(types.KeyboardButton('Отменить удаление пользователя'))

    confirmation_message = (
        f"Информация о пользователе:\n\n"
        f"ФИО: {fio}\n"
        f"Номер телефона: {phone}\n"
        f"Роль: {role}\n\n"
        f"⚠️ ВНИМАНИЕ: Удаление пользователя необратимо! Вы уверены, что хотите удалить этого пользователя?"
    )

    safe_send_message(chat_id, confirmation_message, reply_markup=markup)
    bot.register_next_step_handler(message, process_delete_confirmation)


def process_delete_confirmation(message):
    chat_id = message.chat.id
    confirmation = message.text.strip()

    # Проверяем, не нажата ли кнопка отмены
    if confirmation == 'Отменить удаление пользователя':
        safe_send_message(chat_id, '❌ Удаление пользователя отменено.',
                          reply_markup=types.ReplyKeyboardRemove())
        # Возвращаемся в админ-панель
        from app.bot.handlers import admin_panel
        admin_panel(message)
        return

    # Проверяем подтверждение
    if confirmation != 'Да, я абсолютно уверен':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(types.KeyboardButton('Да, я абсолютно уверен'))
        markup.row(types.KeyboardButton('Отменить удаление пользователя'))
        safe_send_message(chat_id, '❌ Неверное подтверждение. Пожалуйста, используйте кнопки.', reply_markup=markup)
        bot.register_next_step_handler(message, process_delete_confirmation)
        return

    # Удаляем пользователя из БД
    user_data = temp_delete_users[chat_id].get('user_data', {})
    phone = user_data.get('phone_number', '')

    try:
        from app.database.crud import delete_user_db
        delete_user_db(phone)

        fio = f"{user_data.get('last_name', '')} {user_data.get('first_name', '')} {user_data.get('surname', '')}"
        safe_send_message(chat_id, f'✅ Пользователь {fio} успешно удален!',
                          reply_markup=types.ReplyKeyboardRemove())
    except Exception as e:
        safe_send_message(chat_id, f'❌ Ошибка при удалении пользователя: {str(e)}',
                          reply_markup=types.ReplyKeyboardRemove())
    finally:
        # Очищаем временные данные
        if chat_id in temp_delete_users:
            del temp_delete_users[chat_id]

        # Возвращаемся в админ-панель
        from app.bot.handlers import admin_panel
        admin_panel(message)