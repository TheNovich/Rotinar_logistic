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