import logging
from logging.config import fileConfig

from psycopg2 import OperationalError
from psycopg2.extras import DictCursor

import singleton

fileConfig('logging.ini', disable_existing_loggers=False)
log = logging.getLogger(__name__)

si = singleton.Singleton()


def get_user_by_user_id(user_id):
    sql = '''id, user_id, username, first_name, last_name, middle_name
    from users
    where user_id = %s;
    '''
    try:
        with si.db.getconn() as conn:  # return connection without close
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(sql, [user_id])
                res = cursor.fetchone()
    except OperationalError:
        log.exception(f"Ошибка получения пользователя с UID: '{user_id}' из таблицы 'users'")
    else:
        return res
    finally:
        si.db.putconn(conn)


def users_add_new_from_bot(user_id, username, first_name, last_name, middle_name):
    sql = '''INSERT INTO users
    (user_id, username, first_name, last_name, middle_name) 
    values (%s, %s, %s, %s, %s)
    on conflict (user_id) do nothing;
    '''
    try:
        with si.db.getconn() as conn:
            with conn.cursor() as cursor:
                data = [user_id, username, first_name, last_name, middle_name]
                cursor.execute(sql, data)
            conn.commit()
    except OperationalError:
        log.exception(f"Ошибка добавления пользователя: '{username}' в таблицу 'users'")
    finally:
        si.db.putconn(conn)
