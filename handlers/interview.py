"""
ТЗ 5.0: Собеседование ұйымдастыру және уақытты келісу сценарийі.
Кандидат пен Работодатель арасындағы диалогты автоматты түрде басқарады.
"""
from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from database.db_helper import AsyncSessionLocal
from database.models import Vacancy, User, Resume
from services.google_sheets import sheets_sync

interview_router = Router()

class InterviewSetupState(StatesGroup):
    waiting_for_time = State() # Работодательден бос уақытты күту күйі
    waiting_for_cand_confirm = State() # Кандидаттың растауын күту


@interview_router.callback_query(F.data.startswith("match_yes_"))
async def candidate_accepts_vacancy(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """ТЗ 5.1: Кандидат вакансияға бару үшін 'Да' батырмасын басты"""
    await callback.answer()
    vacancy_id = int(callback.data.split("_")[2])
    
    async with AsyncSessionLocal() as session:
        # Вакансия мен оның иесін (Работодатель) анықтау
        vac_result = await session.execute(select(Vacancy).where(Vacancy.id == vacancy_id))
        vacancy = vac_result.scalar_one_or_none()
        
        # Кандидаттың анкет мәліметтерін алу
        cand_result = await session.execute(select(Resume).join(User).where(User.telegram_id == callback.from_user.id))
        resume = cand_result.scalar_one_or_none()
        
        if vacancy and resume:
            # Работодательдің TG ID-сін табу
            emp_user_result = await session.execute(select(User).where(User.id == vacancy.employer_id))
            employer_user = emp_user_result.scalar_one_or_none()
            
            if employer_user:
                # ТЗ 5.1 бойынша Работодательге хабарлама жіберу
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🗓 Назначить время", callback_data=f"set_time_{resume.id}_{vacancy.id}")]
                ])
                
                await bot.send_message(
                    chat_id=employer_user.telegram_id,
                    text=f"🎯 **Найден кандидат на вакансию [{vacancy.position}]!**\n\n"
                         f"👤 Имя: {resume.name}\n"
                         f"⏳ Опыт: {resume.experience} лет\n"
                         f"📞 Контакт: {resume.contact}\n\n"
                         f"Хотите назначить собеседование?",
                    reply_markup=kb,
                    parse_mode="Markdown"
                )
                
                await callback.message.edit_text("⏳ **Отлично! Мы уведомили работодателя.** Ожидайте предложений по времени собеседования.")
                
                # ТЗ 9.3: Google Таблицаға мәліметті жіберу (Мәртебесі өзгерді)
                await sheets_sync.sync_interview(
                    cand_name=resume.name, vacancy_title=vacancy.position, 
                    company=vacancy.company_name, date_str="В процессе", time_str="В процессе", status="Предложена вакансия"
                )


@interview_router.callback_query(F.data.startswith("set_time_"))
async def employer_starts_time_setup(callback: CallbackQuery, state: FSMContext):
    """Работодатель уақыт белгілеу батырмасын басты"""
    await callback.answer()
    _, _, resume_id, vacancy_id = callback.data.split("_")
    
    # Күйге деректерді сақтап қоямыз, себебі келесі хабарламада мәтін түрінде уақытты жазады
    await state.set_state(InterviewSetupState.waiting_for_time)
    await state.update_data(resume_id=int(resume_id), vacancy_id=int(vacancy_id), employer_msg_id=callback.message.message_id)
    
    await callback.message.answer("📝 **ТЗ 5.2:** Введите свободное время для собеседования текстом.\n*Пример: 15 июня в 15:00 или Завтра в 11:00*", parse_mode="Markdown")


@interview_router.message(InterviewSetupState.waiting_for_time)
async def employer_proposes_time(message: Message, state: FSMContext, bot: Bot):
    """ТЗ 5.2: Работодатель уақытты жазды, оны кандидатқа ұсынамыз"""
    proposed_time = message.text
    data = await state.get_data()
    
    async with AsyncSessionLocal() as session:
        resume = (await session.execute(select(Resume).where(Resume.id == data["resume_id"]))).scalar_one_or_none()
        vacancy = (await session.execute(select(Vacancy).where(Vacancy.id == data["vacancy_id"]))).scalar_one_or_none()
        cand_user = (await session.execute(select(User).where(User.id == resume.user_id))).scalar_one_or_none()
        
        if resume and vacancy and cand_user:
            # Кандидатқа уақытты бекіту батырмасын ұсыну
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Подтвердить встречу", callback_data=f"cand_confirm_{vacancy.id}_{data['resume_id']}"),
                    InlineKeyboardButton(text="❌ Отклонить", callback_data="cand_reject_time")
                ]
            ])
            
            # FSM-де уақытты сақтаймыз
            await state.update_data(proposed_time=proposed_time)
            
            await bot.send_message(
                chat_id=cand_user.telegram_id,
                text=f"📅 **Работодатель предложил время для собеседования!**\n\n"
                     f"🏢 Компания: {vacancy.company_name}\n"
                     f"💼 Должность: {vacancy.position}\n"
                     f"⏰ **Время:** {proposed_time}\n"
                     f"📍 **Адрес:** {vacancy.address}\n\n"
                     f"Вам подходит это время?",
                reply_markup=kb,
                parse_mode="Markdown"
            )
            await message.answer("🚀 Время отправлено кандидату на подтверждение!")


@interview_router.callback_query(F.data.startswith("cand_confirm_"))
async def candidate_final_confirmation(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """ТЗ 5.3: Кандидат уақытты мақұлдады, кездесу ресми бекітілді!"""
    await callback.answer()
    _, _, vacancy_id, resume_id = callback.data.split("_")
    data = await state.get_data()
    time_final = data.get("proposed_time", "Уточняется")
    
    async with AsyncSessionLocal() as session:
        vacancy = (await session.execute(select(Vacancy).where(Vacancy.id == int(vacancy_id)))).scalar_one_or_none()
        resume = (await session.execute(select(Resume).where(Resume.id == int(resume_id)))).scalar_one_or_none()
        emp_user = (await session.execute(select(User).where(User.id == vacancy.employer_id))).scalar_one_or_none()
        
        # 1. Кандидатқа растау (ТЗ 5.3)
        await callback.message.edit_text(
            f"🎉 **Вы записаны на собеседование!**\n\n"
            f"📍 Адрес: {vacancy.address if vacancy else '-'}\n"
            f"⏰ Время: {time_final}\n\n"
            f"Удачи! Бот напомнит вам о встрече заранее. 🔔"
        )
        
        # 2. Работодательге растау (ТЗ 5.3)
        if emp_user:
            await bot.send_message(
                chat_id=emp_user.telegram_id,
                text=f"✅ **Кандидат {resume.name if resume else ''} записан на собеседование!**\n\n"
                     f"💼 Должность: {vacancy.position}\n"
                     f"⏰ Время: {time_final}"
            )
            
        # 3. ТЗ 9.3: Google Sheets-ке ресми сәтті жазба жазу
        await sheets_sync.sync_interview(
            cand_name=resume.name if resume else "Кандидат",
            vacancy_title=vacancy.position if vacancy else "Должность",
            company=vacancy.company_name if vacancy else "Компания",
            date_str=datetime.now().strftime("%Y-%m-%d"),
            time_str=time_final,
            status="Приглашен"
        )
        
    await state.clear()