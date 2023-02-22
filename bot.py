# from aiogram import Router
from aiogram.types import *

from misc import bot

import logging
from logging.config import fileConfig


fileConfig('logging.ini', disable_existing_loggers=False)
log = logging.getLogger(__name__)
# router = Router()


# Регистрация команд, отображаемых в интерфейсе Telegram
async def set_commands():
    commands = [
        BotCommand(command="/add", description="Добавить покупку"),
        BotCommand(command="/help", description="Справка"),
        BotCommand(command="/stat", description="Статистика"),
    ]
    log.info(f'Установлен список команд BotCommandScopeDefault()')
    await bot.set_my_commands(commands, BotCommandScopeDefault())
    commands2 = [
        BotCommand(command="/top", description="Топ"),
    ]
    log.info(f'Установлен список команд BotCommandScopeChat(chat_id=4210135)')
    await bot.set_my_commands(commands2, BotCommandScopeChat(chat_id=4210135))


async def send_msg2isaroot(msg):
    await bot.send_message(chat_id=4210135, text=msg)
    print()
