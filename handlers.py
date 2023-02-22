import asyncio
import logging
import re
from datetime import datetime, timedelta
from logging.config import fileConfig

from aiogram import types, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db import users as udb
from cb_data import CallbackTopRace, CallbackGuildRace, CallbackGuildList
from misc import bot

fileConfig('logging.ini', disable_existing_loggers=False)
log = logging.getLogger(__name__)
router = Router()


@router.message(F.chat.type == 'private', Command(commands="start"))
async def cmd_start(message: types.Message):
    mc = message.chat
    # id, user_id, username, first_name, last_name, middle_name
    us = udb.get_user_by_user_id(mc.id)
    if us is None:
        log.info(f'Регистрация нового пользователя {mc.username or ""} (id:{mc.id})')
        await message.answer("Добро пожаловать, хотя не знаю чем смогу помочь 🥲")
        return
    if mc.username is not None:
        db.update_users_tg_username(us[0], mc.username)
    if us[5] != '🤖':
        log.warning(f'Попытка запустить бот игроком {us[5]}{us[3]}: @{mc.username} (id:{mc.id})')
        await message.answer("Запрос этой информации недоступен для вашей расы!\r\nЖдем вас в Аккретии")
        return
    if us[12] == 0:
        pass
    log.info(f'Авторизация игрока {us[5]}{us[3]}: @{mc.username} (id:{mc.id})')
    await message.answer(f'Добро пожаловать {us[3]}')


@router.message(F.chat.type == 'private', Command(commands=['help']))
async def cmd_help(message: types.Message):
    txt = """
Используйте команду /add для добавления новой покупки.
Используйте команду /stat для просмотра статистики
Бот пока не сильно умный, более ничего еще не умеет, увы.
"""
    mc = message.chat
    log.info(f'Вызов справки пользователем @{mc.username} id:{mc.id}')
    await message.answer(txt)


@router.message(F.chat.type == 'private', Command(commands=['top']))
async def cmd_top_cw_activity(message: types.Message):
    log.info('top command')
    mgc = message.get_current()
    mc = message.chat
    mu = message.from_user

    # id, user_id, username, name, guild_id, race, lvl, action_dt, cw_dt, castle_dt, activity, lamp
    us = db.get_from_users_by_user_id(mc.id)
    if us is None:
        log.warning(f'Запрошена команда справки по топам неизвестным пользователем {mc.username} (id:{mc.id})')
        await message.answer("Кажется я вас не знаю!\r\nСовершите любое действие отражаемое в rf_actions и повторите "
                             "попытку после появления там.\r\nК сожалению другие методы авторизации пока недоступны.")
        return
    if mc.username is not None:
        if us[2] != mc.username:
            db.update_users_tg_username(us[0], mc.username)
    if us[5] != '🤖':
        log.warning(f'Запрос информации по по топам игроком {us[5]}{us[3]}: @{mc.username} (id:{mc.id})')
        await message.answer("Запрос этой информации недоступен для вашей расы!")
        return
    if us[6] <= 53 and us[12] == 0:  # TODO: Костыль для чв-водов, открывает доступ по полю регистеред = 1
        log.warning(f'Запрос информации по гильдиям игроком {us[6]} уровня {us[5]}{us[3]}: @{mc.username} (id:{mc.id})')
        await message.answer("Запрос этой информации временно недоступен для вашего уровня!")
        return
    rcs = db.get_guild_races()
    rc = ['👩‍🚀', '🧝‍♀', '🤖']
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=rc[0], callback_data=CallbackTopRace(race=rc[0]))
    keyboard.button(text=rc[1], callback_data=CallbackTopRace(race=rc[1]))
    keyboard.button(text=rc[2], callback_data=CallbackTopRace(race=rc[2]))
    keyboard.adjust(3)
    log.debug(rcs)
    await message.answer("Выберите расу", reply_markup=keyboard.as_markup())


@router.callback_query(CallbackTopRace.filter())
async def callbacks_get_top_race_user_list(call: types.CallbackQuery, callback_data: CallbackTopRace):
    race = callback_data.race
    dt_now = datetime.utcnow()
    msk_td = timedelta(hours=3)
    week_td = timedelta(days=7)
    date_of_period = dt_now + msk_td - week_td
    low_bound = 7
    # race, lamp, guild_name, name, lvl, battle_count, wins, looses
    user_list = db.get_top_wariors_last_week_by_race(race, date_of_period, low_bound)
    if len(user_list) == 0:
        await call.message.edit_text(f'¯\\_(ツ)_/¯\r\nНулевая активность по расе {race}')
        await call.answer("¯\\_(ツ)_/¯")
    else:
        text = f'Топ расы {race} \r\n'
        users_text = ''
        i: int = 1
        top_kills = 0
        top_deaths = 0
        for usr in user_list:
            gi = "[" + usr[2] + "]" or ""
            users_text += f'{i:02}) 🏅{usr[4]} {usr[1] or ""} {gi}{usr[3]}: 🌋 {usr[5]} ⚔️ {usr[6]} ☠️ {usr[7]}\r\n'
            i += 1
            top_kills += usr[6]
            top_deaths += usr[7]
            if i > 30:
                break
        text += f'⚔️ {top_kills} ☠️ {top_deaths}\r\n\r\n'
        text += users_text
        log.info(f'Запрос информации пользователем @{call.message.chat.username} по расе {race}:\r\n{text}')
        await call.message.edit_text(f'{text}')
        await call.answer()


async def is_user_allowed(message: types.Message):
    mc = message.chat
    # id, user_id, username, name, guild_id, race, lvl, action_dt, cw_dt, castle_dt, activity, lamp, registered
    us = db.get_from_users_by_user_id(mc.id)
    if us is None:
        log.warning(f'Запрошена команда справки по гильдиям неизвестным пользователем {mc.username} (id:{mc.id})')
        await message.answer("Кажется я вас не знаю!\r\nСовершите любое действие отражаемое в rf_actions и повторите "
                             "попытку после появления там.\r\nК сожалению другие методы авторизации пока недоступны.")
        return False
    if mc.username is not None:
        if us[2] != mc.username:
            db.update_users_tg_username(us[0], mc.username)
    if us[5] != '🤖':
        log.warning(f'Запрос информации по гильдиям игроком {us[5]}{us[3]}: @{mc.username} (id:{mc.id})')
        await message.answer("Запрос этой информации недоступен для вашей расы!")
        return False
    if us[6] <= 53 and us[12] == 0:  # TODO: Костыль для чв-водов, открывает доступ по полю регистеред = 1
        log.warning(f'Запрос информации по гильдиям игроком {us[6]} уровня {us[5]}{us[3]}: @{mc.username} (id:{mc.id})')
        await message.answer("Запрос этой информации временно недоступен для вашего уровня!")
        return False
    return True


@router.message(F.chat.type == 'private', Command(commands=['warriors']))
async def cmd_warriors(message: types.Message, command: CommandObject):
    log.info('warriors command')
    log.info(command.args)
    gi_warriors_args = command.args
    is_allow = await is_user_allowed(message)
    if not is_allow:
        return
    elif gi_warriors_args is None:
        await select_warriors_race(message)
    elif ' ' in gi_warriors_args:
        await select_warriors_gi_date(message, gi_warriors_args)
    else:
        await select_warriors_gi(message, gi_warriors_args)


async def select_warriors_race(message: types.Message):
    rcs = db.get_guild_races()
    rc = ['👩‍🚀', '🧝‍♀', '🤖']
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=rc[0], callback_data=CallbackGuildRace(race=rc[0]))
    keyboard.button(text=rc[1], callback_data=CallbackGuildRace(race=rc[1]))
    keyboard.button(text=rc[2], callback_data=CallbackGuildRace(race=rc[2]))
    keyboard.adjust(3)
    log.debug(rcs)
    await message.answer("Выберите расу запрашиваемой гильдии", reply_markup=keyboard.as_markup())


async def select_warriors_gi(message: types.Message, gi: str):
    days = 7
    texts = await warriors_gi_date(message, gi, days)
    for text in texts:
        await message.answer(text)
    log.info(f'Запрос информации пользователем @{message.chat.username} по гильдии {gi}:\r\n{texts}')


async def select_warriors_gi_date(message: types.Message, arg_string: str):
    pattern_gi_date = re.compile(r'(.*?) (\d+)')
    res = re.search(pattern_gi_date, arg_string)
    if res is None:
        await message.answer('Ошибка запроса')
        return
    gi = res.group(1)
    days = int(res.group(2))
    texts = await warriors_gi_date(message, gi, days)
    for text in texts:
        await message.answer(text)
        log.info(f'Запрос информации пользователем @{message.chat.username} по гильдии {gi}:\r\n{text}')


async def warriors_gi_date(message: types.Message, gi, days):
    gi_id = []
    # guild_id, guild_name, race
    guilds = db.get_guild_by_name(gi)
    if len(guilds) != 0:
        gi_id.append(guilds[0])
    else:
        # guild_id, guild_name, race
        guilds = db.get_guild_by_lower_name(gi)
        if len(guilds) != 0:
            gi_id.append(guilds[0])
        else:
            guilds = db.get_guilds_by_instr_name(gi)
            if len(guilds) != 0:
                for g in guilds:
                    gi_id.append(g[0])
    if len(gi_id) == 0:
        await message.answer('¯\\_(ツ)_/¯\r\nГильдия не найдена')
        return []
    dt_now = datetime.utcnow()
    msk_td = timedelta(hours=3)
    custom_td = timedelta(days=days)
    date_of_period = dt_now + msk_td - custom_td
    texts = []
    for guild_id in gi_id:
        user_list = db.get_cw_warriors_by_guild_id_and_date_of(guild_id, date_of_period)
        text = await gi_users2text_message(guild_id, user_list)
        texts.append(text)
    return texts


async def gi_users2text_message(guild_id, user_list: list):
    guild_name = db.get_guild_name_by_id(guild_id)
    if len(user_list) == 0:
        return f'¯\\_(ツ)_/¯\r\nНулевая активность по гильдии {guild_name}'
    usl = user_list[0]
    text = f'{usl[0]}{guild_name} \r\n🏅'
    users_text = '\r\n\r\n'
    i: int = 1
    users = {}
    for usr in user_list:
        users_text += f'{i}) 🏅{usr[3]} {usr[1]}{usr[2]}: 🌋 {usr[4]} ⚔️ {usr[5]} ☠️ {usr[6]}\r\n'
        i += 1
        if usr[3] not in users.keys():
            users[usr[3]] = 0
        users[usr[3]] = users.get(usr[3]) + 1
    for k in users.keys():
        text += f'{k}x{users.get(k)} '
    text += users_text
    return text


@router.callback_query(CallbackGuildRace.filter())
async def callbacks_guild_list_by_race(call: types.CallbackQuery, callback_data: CallbackGuildRace):
    # user_value = user_data.get(call.from_user.id, 0)
    race = callback_data.race
    guild_list = db.get_guilds_by_race(race)
    keyboard = InlineKeyboardBuilder()
    for g in guild_list:
        keyboard.button(text=g[1], callback_data=CallbackGuildList(guild_id=g[0], guild_name=g[1]))

    keyboard.adjust(3)
    log.info(f'Запрос информации пользователем @{call.message.chat.username} по расе {race}')
    await call.message.edit_text(f"Выберите гильдию {race}", reply_markup=keyboard.as_markup())
    await call.answer()


@router.callback_query(CallbackGuildList.filter())
async def callbacks_get_guild_user_list(call: types.CallbackQuery, callback_data: CallbackGuildList):
    guild_id = callback_data.guild_id
    guild_name = callback_data.guild_name
    # db = qmap.get_db()
    # db = rf_db_si.Singleton()
    dt_now = datetime.utcnow()
    msk_td = timedelta(hours=3)
    week_td = timedelta(days=7)
    date_of_period = dt_now + msk_td - week_td
    # race, lamp, name, lvl, battle_count, wins, looses
    user_list = db.get_cw_warriors_by_guild_id_and_date_of(guild_id, date_of_period)
    text = await gi_users2text_message(guild_id, user_list)
    log.info(f'Запрос информации пользователем @{call.message.chat.username} по гильдии {guild_name}:\r\n{text}')
    await call.message.edit_text(f'{text}')
    await call.answer()


