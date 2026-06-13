from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
from database.db_helper import AsyncSessionLocal, get_or_create_user
from database.models import User, WithdrawalRequest
from sqlalchemy import select
from config.settings import settings

class WithdrawalState(StatesGroup):
    waiting_for_phone = State()

@pay_router.callback_query(F.data == "choose_tariff_employer")
async def show_employer_tariffs(callback: CallbackQuery):
    """ТЗ 10.1: Работодательге тарифтерді ұсыну"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💼 Базовый (20 канд. / 10k тг)", callback_data="buy_emp_base")],
        [InlineKeyboardButton(text="🚀 Расширенный (50 канд. / 20k тг)", callback_data="buy_emp_adv")]
    ])
    await callback.message.answer("💳 **Выберите тарифный план для поиска сотрудников:**", reply_markup=kb)

@pay_router.callback_query(F.data.startswith("buy_emp_"))
async def process_employer_invoice(callback: CallbackQuery, bot: Bot):
    """Төлем шотын құру (Базовый немесе Расширенный)"""
    plan = callback.data.split("_")[2]
    amount = 10000 if plan == "base" else 20000
    title = "Тариф Базовый" if plan == "base" else "Тариф Расширенный"
    
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=title,
        description=f"Доступ к базе кандидатов Smart Chef HR. Лимит: {20 if plan=='base' else 50} открытий.",
        payload=f"employer_{plan}_payload",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=title, amount=amount)]
    )

# Сәтті төлемді қабылдау (Successful Payment өңдеушісіне қосымша логика)
# Төлем сәтті өткенде payload-қа байланысты max_candidates_limit өрісі 20 немесе 50-ге орнатылады.

# ==========================================
# 💸 РЕФЕРАЛДЫҚ БАЛАНСТАН АҚША ШЫҒАРУ (ТЗ 11.5 & 11.6)
# ==========================================

@pay_router.callback_query(F.data == "withdraw_money")
async def start_withdrawal(callback: CallbackQuery, state: FSMContext):
    """Ақша шығару батырмасын басқанда лимитті тексеру"""
    user = await get_or_create_user(callback.from_user.id)
    
    if user.balance < 1000.0:  # ТЗ 11.5: Минималды шығару сомасы — 1000 тг
        await callback.message.answer(f"⚠️ **Минимальная сумма для вывода составляет 1000 тг.**\nВаш текущий баланс: {user.balance} тг.")
        await callback.answer()
        return
        
    await callback.message.answer("💰 Введите номер телефона (Kaspi) для перевода средств:")
    await state.set_state(WithdrawalState.waiting_for_phone)
    await callback.answer()

@pay_router.message(WithdrawalState.waiting_for_phone)
async def process_withdrawal_phone(message: Message, state: FSMContext, bot: Bot):
    phone = message.text
    async with AsyncSessionLocal() as session:
        async with session.begin():
            result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
            user = result.scalar_one_or_none()
            
            if user and user.balance >= 1000.0:
                # Сұранысты базаға жазу
                new_request = WithdrawalRequest(user_id=user.id, amount=user.balance, phone_number=phone)
                session.add(new_request)
                
                # Пайдаланушының балансын нөлдеу
                current_balance = user.balance
                user.balance = 0.0
                
                await message.answer("🚀 **Заявка на вывод успешно отправлена!**\nАдминистратор обработает перевод в течение 24 часов.")
                
                # ТЗ 11.7: Криаторға (Админге) жедел хабарлама жіберу
                try:
                    kb = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="✅ Выплачено", callback_data=f"approve_with_{new_request.id}")]
                    ])
                    await bot.send_message(
                        chat_id=settings.CREATOR_ID,
                        text=f"💸 **Новая заявка на вывод денег!**\n\nUser ID: `{user.telegram_id}`\nСумма: {current_balance} тг\nТелефон (Kaspi): `{phone}`",
                        reply_markup=kb,
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass
    await state.clear()