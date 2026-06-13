"""
Басты драйверлік файл.
Құдіретті Криатор роутері жүйенің ең жоғарғы иерархиясына тіркелді.
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
from handlers.creator import creator_router  # 👑 Криатор хендлерін импорттау
from services.scheduler import scheduler


async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    # Redis және FSM Storage баптау
    redis_client = Redis.from_url(settings.REDIS_URL)
    storage = RedisStorage(redis=redis_client)

    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=storage)

    # PostgreSQL дерекқорын тексеру/құру
    await init_db()

    # Шедулерді іске қосу
    scheduler.start()

    # 👑 РОУТЕРЛЕРДІ ТІРКЕУ (Creator бірінші кезекте тұрады)
    dp.include_router(creator_router)
    dp.include_router(start_router)
    dp.include_router(anketa_router)
    dp.include_router(pay_router)
    dp.include_router(interview_router)

    logging.info("Smart Chef HR: Криатордың шексіз басқару панелі сәтті қосылды!")
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())