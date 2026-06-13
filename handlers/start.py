"""
Басты драйверлік файл.
FSM (Finite State Machine) енді толықтай Redis-ке көшірілді, бот қайта қосылса да деректер жоғалмайды.
"""
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from config.settings import settings
from database.db_helper import init_db
from handlers.start import start_router
from handlers.anketa import anketa_router
from handlers.payments import pay_router
from handlers.interview import interview_router
from services.scheduler import scheduler


async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    # 1. Redis Storage-ді асинхронды инициализациялау (ТЗ-дағы FSM үшін)
    redis_client = Redis.from_url(settings.REDIS_URL)
    storage = RedisStorage(redis=redis_client)

    # Бот пен Диспетчерді (Redis Storage-бен бірге) құру
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=storage)

    # 2. PostgreSQL дерекқорын тексеру және іске қосу
    await init_db()

    # 3. Еске салу шедулерін (Background Scheduler) қосу
    scheduler.start()

    # 4. Роутерлерді тіркеу
    dp.include_router(start_router)
    dp.include_router(anketa_router)
    dp.include_router(pay_router)
    dp.include_router(interview_router)

    logging.info("Smart Chef HR: PostgreSQL және Redis интеграциясы сәтті аяқталды!")
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())