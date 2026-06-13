"""
Жаңартылған Сәйкестендіру жүйесі.
PostgreSQL (asyncpg) үшін толық асинхронды сұраныстармен оңтайландырылған.
"""
from aiogram import Bot
from sqlalchemy import select
from database.db_helper import AsyncSessionLocal
from database.models import Resume, Vacancy, User
from keyboards.inline import get_matching_keyboard


async def check_matching_for_vacancy(vacancy: Vacancy, bot: Bot):
    """ТЗ 4.1: Жаңа вакансияға сай келетін кандидаттарды PostgreSQL-ден асинхронды іздеу"""
    async with AsyncSessionLocal() as session:
        # ilike операторы PostgreSQL-де мәтінді регистрге қарамай іздеу үшін мінсіз жұмыс істейді
        stmt = select(Resume).where(
            Resume.city.ilike(vacancy.city),
            Resume.position.ilike(vacancy.position),
            Resume.experience >= vacancy.experience
        )
        result = await session.execute(stmt)
        candidates = result.scalars().all()

        for cand in candidates:
            # Әр кандидаттың жазылымы (подпискасы) бар-жоғын тексеру
            res_user = await session.execute(select(User).where(User.id == cand.user_id))
            tg_user = res_user.scalar_one_or_none()
            
            if tg_user:
                # ТЗ 10.2: Превью режимді қолдану
                company_display = vacancy.company_name if tg_user.is_subscribed else "*** (Требуется подписка)"
                address_display = vacancy.address if tg_user.is_subscribed else f"район {vacancy.address.split()[0] if vacancy.address else 'города'}"

                text = (
                    f"🔥 **Найдена новая вакансия по вашему профилю!**\n\n"
                    f"💼 Должность: {vacancy.position}\n"
                    f"🏢 Компания: {company_display}\n"
                    f"💵 Зарплата: {vacancy.salary} тг\n"
                    f"📅 График: {vacancy.schedule}\n"
                    f"📍 Адрес: {address_display}\n\n"
                    f"Хотите пойти на собеседование?"
                )
                try:
                    await bot.send_message(
                        chat_id=tg_user.telegram_id,
                        text=text,
                        reply_markup=get_matching_keyboard(vacancy.id),
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass

# check_matching_for_vacancy ішінде немесе кандидаттар тізімін ашқан кезде:
async def increment_employer_view_limit(employer_user_id: int) -> bool:
    """ТЗ 10.5: Работодательдің ашқан кандидаттарын санау және лимиттен асса блоктау"""
    async with AsyncSessionLocal() as session:
        async with session.begin():
            result = await session.execute(select(User).where(User.id == employer_user_id))
            employer = result.scalar_one_or_none()
            
            if employer:
                # Егер лимиті бітсе немесе подпискасы мүлдем жоқ болса
                if employer.opened_candidates_count >= employer.max_candidates_limit:
                    return False
                
                # Лимитті 1-ге арттыру
                employer.opened_candidates_count += 1
                return True
            return False