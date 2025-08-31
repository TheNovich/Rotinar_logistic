'импорт библиотеки pyTelegramBotApi'
from telebot import types

from app.bot.utils import role_required, search_number, on_click_manager_panel, user_verification, supabase, on_click_driver_panel

'Импорт функций из собственного функцинала'
from app.database.crud import set_role_db
from app.bot.utils import save_order_to_db
'''from app.bot.utils import format_order
from app.bot.utils import create_order
from app.bot.utils import temp_orders'''
from app.bot.order_creation import create_order, temp_orders, format_order
from config import config
from app.bot.utils import safe_send_message

from app.bot.instance import bot


'Обаботчик команы /set_role устанавливет новую роль указанному пользователю'
@bot.message_handler(commands=['set_role'])
@role_required('admin')
def set_role(message):
    try:
        _, phone, new_role = message.text.split()
        if search_number(phone) == 0:
            safe_send_message(message.chat.id, "❌ Пользователь с таким номером не найден!")
            return
        set_role_db(new_role, phone)
        safe_send_message(message.chat.id, f"✅ Роль обновлена! Пользователь {phone} теперь {new_role}")
    except:
        safe_send_message(message.chat.id, "❌ Использование: /set_role [phone] [role]")

'Обработчик команды /manager_panel вызывает панель команд доступных для роли manager'

@bot.message_handler(commands=['start'])
def start_handler(message):
    user_verification(message, driver_panel, manager_panel)


@bot.message_handler(commands=['manager_panel'])
@role_required('manager', 'admin')
def manager_panel(message):
    markup = types.ReplyKeyboardMarkup()
    buttons = []
    buttons.append(types.KeyboardButton('Свободные водители'))
    buttons.append(types.KeyboardButton('Все водители'))
    if config.USE_NEW_ORDER_FLOW:
        buttons.append(types.KeyboardButton('📝 Создать заказ'))
    markup.row(*buttons)
    safe_send_message(message.chat.id, 'Выберите действие: ', reply_markup=markup)
    bot.register_next_step_handler(message, lambda msg: on_click_manager_panel(msg, manager_panel))

# Обработчик кнопок подтверждения
@bot.callback_query_handler(func=lambda call: call.data.startswith(('confirm_order_', 'restart_order_')))
def handle_order_confirmation(call):
    chat_id = call.data.split('_')[-1]
    order_data = temp_orders.get(int(chat_id))

    if not order_data:
        bot.answer_callback_query(call.id, "❌ Данные заказа утеряны. Начните заново.")
        return

    if call.data.startswith('confirm_order_'):
        # Сохранение заказа в базе данных
        order_id = save_order_to_db(order_data)

        safe_send_message(
            call.message.chat.id,
            f"✅ *Заказ #{order_id} успешно создан!*\n\n{format_order(order_data)}",
            parse_mode="Markdown",
            reply_markup=types.ReplyKeyboardRemove()
        )
        # Удаляем временные данные
        if int(chat_id) in temp_orders:
            del temp_orders[int(chat_id)]
        manager_panel(call.message)

    else:  # restart_order
        # Удаляем временные данные
        if int(chat_id) in temp_orders:
            del temp_orders[int(chat_id)]
        create_order(call.message, manager_panel)

    bot.answer_callback_query(call.id)

@bot.message_handler(commands=['driver_panel'])
@role_required('driver', 'admin')
def driver_panel(message):
    markup = types.ReplyKeyboardMarkup()
    is_on_shift = supabase.table('users').select('is_on_shift').eq('telegram_id', message.from_user.id).execute()
    driver_state = supabase.table('users').select('state_id').eq('telegram_id', message.from_user.id).execute()
    if is_on_shift.data[0]['is_on_shift'] == False:
        driver_start_button = types.KeyboardButton('Начать смену 🚀')
        markup.row(driver_start_button)
        safe_send_message(message.chat.id, 'Перед началом работы начните смену!')
    else:
        driver_finish_button = types.KeyboardButton('Завершить смену 🏁')
        driver_сancel_order_button = types.KeyboardButton('Отменить заказ ❌')
        driver_break_button = types.KeyboardButton('Перерыв ⏸️')
        driver_end_break = types.KeyboardButton('Завершить перерыв ▶️')

        if driver_state.data[0]['state_id'] == 1:
            driver_loading_car_button = types.KeyboardButton('Перейти к этапу загрузки автомобиля')
            markup.row(driver_loading_car_button)
            markup.row(driver_сancel_order_button)
        elif driver_state.data[0]['state_id'] == 2:
            driver_loading_car_button = types.KeyboardButton('Выдвинуться на точку разгрузки')
            markup.row(driver_loading_car_button)
            markup.row(driver_сancel_order_button)
        elif driver_state.data[0]['state_id'] == 3:
            driver_loading_car_button = types.KeyboardButton('Разгрузка автомобиля')
            markup.row(driver_loading_car_button)
            markup.row(driver_сancel_order_button)
        elif driver_state.data[0]['state_id'] == 4:
            driver_loading_car_button = types.KeyboardButton('Завершить заказ')
            markup.row(driver_loading_car_button)
            markup.row(driver_сancel_order_button)
        elif driver_state.data[0]['state_id'] == 5:
            driver_take_order_button = types.KeyboardButton('Взять заказ')
            markup.row(driver_take_order_button)
            markup.row(driver_finish_button, driver_break_button)
        elif driver_state.data[0]['state_id'] == 6:
            markup.row(driver_end_break)
            markup.row(driver_finish_button)



    safe_send_message(message.chat.id, 'Выберите действие: ', reply_markup=markup)
    bot.register_next_step_handler(message, lambda msg: on_click_driver_panel(msg, driver_panel))
