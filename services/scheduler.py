"""
ТЗ 6.1: Автоматты түрде еске салу жүйесі (Reminders).
APScheduler арқылы собеседованиеге 24 сағат және 2 сағат қалғанда хабарлама жібереді.
"""
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from database.db_helper import AsyncSessionLocal
from database.models import User
from sqlalchemy import select

# Асинхронды шедулерді инициализациялау
scheduler = AsyncIOScheduler()

async def send_interview_reminder(bot: Bot, user_tg_id: int, text: str):
    """Пайдаланушыға еске салу хабарламасын қауіпсіз жіберу"""
    try:
        await bot.send_message(chat_id=user_tg_id, text=text, parse_mode="Markdown")
    except Exception:
        pass  # Ботты блоктап тастаған жағдайда қатені өткізіп жіберу

def schedule_reminders(bot: Bot, candidate_tg_id: int, employer_tg_id: int, interview_time: datetime, address: str):
    """
    Жаңа собеседование бекітілгенде еске салу тапсырмаларын уақыт белгілеп қосу.
    ТЗ 6.1: За 24 часа и За 2 часа.
    """
    now = datetime.now()

    # 24 сағат бұрынғы уақытты есептеу
    time_24h = interview_time - timedelta(hours=24)
    if time_24h > now:
        scheduler.add_job(
            send_interview_reminder,
            'date',
            run_date=time_24h,
            args=[bot, candidate_tg_id, f"🔔 **Напоминание за 24 часа!**\n\nЗавтра у вас собеседование.\n📍 Адрес: {address}\n⏰ Время: {interview_time.strftime('%H:%M')}"]
        )
        scheduler.add_job(
            send_interview_reminder,
            'date',
            run_date=time_24h,
            args=[bot, employer_tg_id, f"🔔 **Напоминание за 24 часа!**\n\nЗавтра у вас собеседование с кандидатом.\n⏰ Время: {interview_time.strftime('%H:%M')}"]
        )

    # 2 hours бұрынғы уақытты есептеу
    time_2h = interview_time - timedelta(hours=2)
    if time_2h > now:
        scheduler.add_job(
            send_interview_reminder,
            'date',
            run_date=time_2h,
            args=[bot, candidate_tg_id, f"⚡ **Напоминание за 2 часа!**\n\nСобеседование состоится совсем скоро.\n📍 Адрес: {address}\n⏰ Время: {interview_time.strftime('%H:%M')}"]
        )
        scheduler.add_job(
            send_interview_reminder,
            'date',
            run_date=time_2h,
            args=[bot, employer_tg_id, f"⚡ **Напоминание за 2 часа!**\n\nКандидат будет у вас через 2 часа.\n⏰ Время: {interview_time.strftime('%H:%M')}"]
        )