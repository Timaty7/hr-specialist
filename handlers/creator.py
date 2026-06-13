"""
👑 КРИАТОР ХЕНДЛЕРІ (Creator Control Panel).
Жүйені басқарудың шексіз мүмкіндіктері осы жерде шоғырланған.
"""
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from database.db_helper import AsyncSessionLocal
from database.models import User, Resume, Vacancy
from sqlalchemy import select, func, update
from middlewares.admin import CreatorOnlyMiddleware

creator_router = Router()

# Осы роутердегі барлық хендлерлерге ТЕК Криатор ғана қол жеткізе алады
creator_router.message.middleware(CreatorOnlyMiddleware())


@creator_router.message(Command("admin"))
async def creator_help_panel(message: Message):
    """Криатордың шексіз басқару менюі мен командалар тізімі"""
    help_text = (
        "👑 **Панель Управления Криатора (Шексіз мүмкіндіктер):**\n\n"
        "📊 `/stats` — Жүйенің жалпы статистикасын көру (Пайдаланушылар, Анкеттер)\n"
        "💳 `/give_sub <user_tg_id>` — Пайдаланушыға тегін 30 күн Full Access беру\n"
        "💰 `/add_balance <user_tg_id> <amount>` — Пайдаланушының реферал балансына ақша қосу\n"
        "🚫 `/ban <user_tg_id>` — Пайдаланушыны жүйеден бұғаттау\n"
        "📢 `/broadcast <текст>` — Боттағы барлық пайдаланушыларға жарнамалық хабарлама жіберу"
    )
    await message.answer(help_text, parse_mode="Markdown")


@creator_router.message(Command("stats"))
async def get_system_stats(message: Message):
    """Жүйенің нақты уақыттағы PostgreSQL-ден алынған аналитикасы"""
    async with AsyncSessionLocal() as session:
        # Жалпы сандарды санау
        total_users = await session.scalar(select(func.count(User.id)))
        total_resumes = await session.scalar(select(func.count(Resume.id)))
        total_vacancies = await session.scalar(select(func.count(Vacancy.id)))
        subscribed_users = await session.scalar(select(func.count(User.id)).where(User.is_subscribed == True))

        stats_text = (
            "📊 **Глобальная аналитика Smart Chef HR:**\n\n"
            f"👤 Всего пользователей в базе: {total_users}\n"
            f"👨‍🍳 Активных резюме соискателей: {total_resumes}\n"
            f"💼 Размещенных вакансий: {total_vacancies}\n"
            f"💳 Пользователей с Премиум (Full Access): {subscribed_users}"
        )
        await message.answer(stats_text, parse_mode="Markdown")


@creator_router.message(Command(prefix="/", commands=["give_sub"]))
async def gift_subscription(message: Message):
    """Шексіз мүмкіндік 1: Кез келген адамға қолмен премиум жазылым беру"""
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("⚠️ Использование: `/give_sub <user_tg_id>`")
        return
    
    target_tg_id = int(args[1])
    async with AsyncSessionLocal() as session:
        async with session.begin():
            result = await session.execute(select(User).where(User.telegram_id == target_tg_id))
            user = result.scalar_one_or_none()
            if user:
                user.is_subscribed = True
                user.subscription_expires = datetime.utcnow() + timedelta(days=30)
                await message.answer(f"✅ Пользователю `{target_tg_id}` успешно выдан **Full Access** на 30 дней!", parse_mode="Markdown")
            else:
                await message.answer("❌ Данный пользователь не найден в базе данных.")


@creator_router.message(Command(prefix="/", commands=["add_balance"]))
async def manual_add_balance(message: Message):
    """Шексіз мүмкіндік 2: Реферал балансына қолмен ақша салу (Мысалы, реферал конкурстары үшін)"""
    args = message.text.split()
    if len(args) < 3 or not args[1].isdigit():
        await message.answer("⚠️ Использование: `/add_balance <user_tg_id> <сумма>`")
        return
    
    target_tg_id = int(args[1])
    amount = float(args[2])
    
    async with AsyncSessionLocal() as session:
        async with session.begin():
            result = await session.execute(select(User).where(User.telegram_id == target_tg_id))
            user = result.scalar_one_or_none()
            if user:
                user.balance += amount
                await message.answer(f"✅ Баланс пользователя `{target_tg_id}` успешно пополнен на **{amount} тг**!", parse_mode="Markdown")
            else:
                await message.answer("❌ Пользователь не найден.")

@creator_router.callback_query(F.data.startswith("approve_with_"))
async def approve_withdrawal_by_creator(callback: CallbackQuery, bot: Bot):
    """ТЗ 11.7: Админ 'Выплачено' батырмасын басқанда мәртебені өзгерту және пайдаланушыға сүйінші хабар жіберу"""
    req_id = int(callback.data.split("_")[2])
    
    async with AsyncSessionLocal() as session:
        async with session.begin():
            req_result = await session.execute(select(WithdrawalRequest).where(WithdrawalRequest.id == req_id))
            req = req_result.scalar_one_or_none()
            
            if req and req.status == "Pending":
                req.status = "Approved"
                
                # Пайдаланушыға хабарлау
                user_res = await session.execute(select(User).where(User.id == req.user_id))
                user = user_res.scalar_one_or_none()
                
                if user:
                    try:
                        await bot.send_message(
                            chat_id=user.telegram_id,
                            text=f"✅ **Выплата произведена успешно!**\nСумма **{req.amount} тг** переведена на ваш Kaspi номер `{req.phone_number}`. Спасибо, что вы с нами! 🎁"
                        )
                    except Exception:
                        pass
                
                await callback.message.edit_text(f"✅ Заявка №{req_id} официально одобрена и выплачена!")
    await callback.answer()
