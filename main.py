import asyncio
import logging
from logging.config import fileConfig

import psycopg2
from psycopg2 import pool
from aiogram import Dispatcher

import handlers

import bot
import config
import misc
import singleton

fileConfig('logging.ini', disable_existing_loggers=False)
log = logging.getLogger(__name__)


def create_connection_pool(schema="public"):
    try:
        thread_pg_pool = psycopg2.pool.ThreadedConnectionPool(1, 100, user=config.pg_db_user,
                                                              password=config.pg_db_password,
                                                              host=config.pg_db_host,
                                                              port=config.pg_db_port,
                                                              database=config.pg_db_database,
                                                              options=f"-c search_path={schema}")
        if thread_pg_pool:
            log.info("Connection pool created successfully using ThreadedConnectionPool")
    except (Exception, psycopg2.DatabaseError) as error:
        log.error("Error while connecting to PostgreSQL", error)
    else:
        return thread_pg_pool


# Запуск процесса поллинга новых апдейтов
async def main():
    si = singleton.Singleton()
    si.db = create_connection_pool(config.pg_db_schema)
    log.info("Запуск приложения.")
    dp = Dispatcher()
    try:
        await bot.set_commands()
        dp.include_router(handlers.router)
        await dp.start_polling(misc.bot)
    except TypeError:
        log.error("Цикл main был завершен по невнятным причинам")
    except KeyboardInterrupt:
        log.error("Цикл main был завершен клавиатурной прерывашкой")
    except RuntimeError:
        log.error("Цикл main был завершен в рантайме")


if __name__ == "__main__":
    asyncio.run(main())
