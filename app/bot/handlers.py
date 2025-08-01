'импорт библиотеки pyTelegramBotApi'
from telebot import types

from app.bot.utils import role_required, search_number, on_click_manager_panel, user_verification, supabase, on_click_driver_panel

'Импорт функций из собственного функцинала'
from app.database.crud import set_role_db


from app.bot.instance import bot


'Обаботчик команы /set_role устанавливет новую роль указанному пользователю'
@bot.message_handler(commands=['set_role'])
@role_required('admin')
def set_role(message):
    try:
        _, phone, new_role = message.text.split()
        if search_number(phone) == 0:
            bot.reply_to(message, "❌ Пользователь с таким номером не найден!")
            return
        set_role_db(new_role, phone)
        bot.reply_to(message, f"✅ Роль обновлена! Пользователь {phone} теперь {new_role}")
    except:
        bot.reply_to(message, "❌ Использование: /set_role [phone] [role]")

'Обработчик команды /manager_panel вызывает панель команд доступных для роли manager'
@bot.message_handler(commands=['manager_panel'])
@role_required('manager', 'admin')
def manager_panel(message):
    markup = types.ReplyKeyboardMarkup()
    free_drivers_button = types.KeyboardButton('Свободные водители')
    markup.row(free_drivers_button)
    bot.send_message(message.chat.id, 'Выберите действие', reply_markup=markup)
    bot.register_next_step_handler(message, on_click_manager_panel)

@bot.message_handler(commands=['start'])
def start_handler(message):
    user_verification(message, driver_panel, manager_panel)


@bot.message_handler(commands=['manager_panel'])
@role_required('manager', 'admin')
def manager_panel(message):
    markup = types.ReplyKeyboardMarkup()
    free_drivers_button = types.KeyboardButton('Свободные водители')
    markup.row(free_drivers_button)
    bot.send_message(message.chat.id, 'Выберите действие', reply_markup=markup)
    bot.register_next_step_handler(message, lambda msg: on_click_manager_panel(msg, manager_panel))

@bot.message_handler(commands=['driver_panel'])
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
    bot.register_next_step_handler(message, lambda msg: on_click_driver_panel(msg, driver_panel))
