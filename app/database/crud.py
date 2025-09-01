from supabase import create_client
from config import config

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

'Функция проверки роли пользователя. Возвращает роль пользователя'
def check_user_role(telegram_id):
    user = supabase.table('users').select('role').eq('telegram_id', telegram_id).execute()
    return user.data[0]['role'] if user.data else None

'Функция изменения роли пользоватля в дб'
def set_role_db(new_role, phone):
    supabase.table('users').update({'role': new_role}).eq('phone_number', phone).execute()

def switch_driver_status (next_status_id, telegram_id):
    supabase.table('users').update({'state_id': next_status_id}).eq('telegram_id', telegram_id).execute()

def switch_driver_shift (is_on_shift, telegram_id):
    supabase.table('users').update({'is_on_shift': is_on_shift}).eq('telegram_id', telegram_id).execute()

def update_data_tg_id(table, data, phone):
    supabase.table(table).update(data).eq('phone_number', phone).execute()


def search_number(phone):
    response = supabase.table('users').select('phone_number', count='exact').eq('phone_number', phone).execute()
    return response.count


def create_user(phone_number, first_name, last_name, surname, role):
    user_data = {
        'phone_number': phone_number,
        'first_name': first_name,
        'last_name': last_name,
        'surname': surname,
        'role': role
    }

    # Добавляем поля по умолчанию для водителей
    if role == 'driver':
        user_data['state_id'] = 5
        user_data['is_on_shift'] = False

    response = supabase.table('users').insert(user_data).execute()
    return response

def delete_user_db(phone_number):
    response = supabase.table('users').delete().eq('phone_number', phone_number).execute()
    return response