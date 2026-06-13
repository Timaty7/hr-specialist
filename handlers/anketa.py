"""
Толық FSM анкетілеу жүйесі. Работодатель қадамдары аяқталды және автоматты matching қосылды.
"""
from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from database.db_helper import AsyncSessionLocal, get_or_create_user
from database.models import Resume, Vacancy
from keyboards.inline import get_confirm_keyboard, get_payment_keyboard
from services.matching import check_matching_for_vacancy

anketa_router = Router()

# --- FSM Күйлері ---
class CandidateForm(StatesGroup):
    name = State()
    age = State()
    city = State()
    position = State()
    experience = State()
    prev_jobs = State()
    schedule = State()
    salary = State()
    contact = State()


class EmployerForm(StatesGroup):
    company_name = State()
    city = State()
    position = State()
    requirements = State()
    conditions = State()
    salary = State()
    schedule = State()
    address = State()
    contact_person = State()
    phone = State()


# ==========================================
# 👨‍🍳 СЦЕНАРИЙ: СОИСКАТЕЛЬ (КАНДИДАТ)
# ==========================================

@anketa_router.callback_query(F.data == "role_candidate")
async def start_candidate_fsm(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await callback.message.answer("📝 **Шаг 1 из 9:** Введите ваше имя и фамилию:", parse_mode="Markdown")
    await state.set_state(CandidateForm.name)


@anketa_router.message(CandidateForm.name)
async def process_cand_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("🔢 **Шаг 2 из 9:** Укажите ваш возраст:")
    await state.set_state(CandidateForm.age)


@anketa_router.message(CandidateForm.age)
async def process_cand_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ Пожалуйста, введите корректный возраст (цифрами):")
        return
    await state.update_data(age=int(message.text))
    await message.answer("🌆 **Шаг 3 из 9:** Введите ваш город проживания:")
    await state.set_state(CandidateForm.city)


@anketa_router.message(CandidateForm.city)
async def process_cand_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer("🧑‍🍳 **Шаг 4 из 9:** Какую должность вы желаете занять? (например: Повар горячего цеха):")
    await state.set_state(CandidateForm.position)


@anketa_router.message(CandidateForm.position)
async def process_cand_position(message: Message, state: FSMContext):
    await state.update_data(position=message.text)
    await message.answer("⏳ **Шаг 5 из 9:** Ваш опыт работы в годах (цифрой, например: 3):")
    await state.set_state(CandidateForm.experience)


@anketa_router.message(CandidateForm.experience)
async def process_cand_exp(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ Введите число лет опыта работы цифрами:")
        return
    await state.update_data(experience=int(message.text))
    await message.answer("🏢 **Шаг 6 из 9:** Опишите ваши предыдущие места работы:")
    await state.set_state(CandidateForm.prev_jobs)


@anketa_router.message(CandidateForm.prev_jobs)
async def process_cand_jobs(message: Message, state: FSMContext):
    await state.update_data(prev_jobs=message.text)
    await message.answer("📅 **Шаг 7 из 9:** Желаемый график работы (например: Сменный 2/2 или Полный день):")
    await state.set_state(CandidateForm.schedule)


@anketa_router.message(CandidateForm.schedule)
async def process_cand_schedule(message: Message, state: FSMContext):
    await state.update_data(schedule=message.text)
    await message.answer("💵 **Шаг 8 из 9:** Ожидаемая заработная плата (в тенге, цифрами):")
    await state.set_state(CandidateForm.salary)


@anketa_router.message(CandidateForm.salary)
async def process_cand_salary(message: Message, state: FSMContext):
    if not message.text.replace(" ", "").isdigit():
        await message.answer("⚠️ Укажите сумму цифрами:")
        return
    await state.update_data(salary=int(message.text.replace(" ", "")))
    await message.answer("📞 **Шаг 9 из 9:** Оставьте ваши контакты для связи (Телефон / WhatsApp):")
    await state.set_state(CandidateForm.contact)


@anketa_router.message(CandidateForm.contact)
async def save_candidate_form(message: Message, state: FSMContext):
    await state.update_data(contact=message.text)
    data = await state.get_data()
    
    # Пайдаланушыға толтырылған деректерді көрсету (Preview)
    preview_text = (
        f"🏁 **Проверьте вашу анкету соискателя:**\n\n"
        f"👤 Имя: {data['name']}\n"
        f"🔢 Возраст: {data['age']}\n"
        f"🏙 Город: {data['city']}\n"
        f"💼 Должность: {data['position']}\n"
        f"⏳ Опыт: {data['experience']} лет\n"
        f"🏢 Прошлое место работы: {data['prev_jobs']}\n"
        f"📅 График: {data['schedule']}\n"
        f"💵 Зарплата: {data['salary']} тг\n"
        f"📞 Контакт: {data['contact']}\n\n"
        f"✨ *Все данные будут сохранены в базе данных.*"
    )
    await message.answer(preview_text, reply_markup=get_confirm_keyboard(), parse_mode="Markdown")   company_name, city, position, requirements, conditions, salary, schedule, address, contact_person, phone = [State() for _ in range(10)]


# ==========================================
# 💼 СЦЕНАРИЙ: РАБОТОДАТЕЛЬ (ТОЛЫҚ НҰСҚАСЫ)
# ==========================================

@anketa_router.callback_query(F.data == "role_employer")
async def start_employer_fsm(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await callback.message.answer("🏢 **Шаг 1 из 10:** Введите Название вашей компании:")
    await state.set_state(EmployerForm.company_name)

@anketa_router.message(EmployerForm.company_name)
async def process_emp_company(message: Message, state: FSMContext):
    await state.update_data(company_name=message.text)
    await message.answer("🌆 **Шаг 2 из 10:** Введите город поиска сотрудников:")
    await state.set_state(EmployerForm.city)

@anketa_router.message(EmployerForm.city)
async def process_emp_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer("🧑‍🍳 **Шаг 3 из 10:** Какая должность требуется? (например: Повар-универсал):")
    await state.set_state(EmployerForm.position)

@anketa_router.message(EmployerForm.position)
async def process_emp_pos(message: Message, state: FSMContext):
    await state.update_data(position=message.text)
    await message.answer("📝 **Шаг 4 из 10:** Укажите Требования к кандидату (опыт, навыки):")
    await state.set_state(EmployerForm.requirements)

@anketa_router.message(EmployerForm.requirements)
async def process_emp_req(message: Message, state: FSMContext):
    await state.update_data(requirements=message.text)
    await message.answer("🌟 **Шаг 5 из 10:** Укажите Условия работы:")
    await state.set_state(EmployerForm.conditions)

@anketa_router.message(EmployerForm.conditions)
async def process_emp_cond(message: Message, state: FSMContext):
    await state.update_data(conditions=message.text)
    await message.answer("💵 **Шаг 6 из 10:** Предлагаемая Зарплата (в тенге, только цифры):")
    await state.set_state(EmployerForm.salary)

@anketa_router.message(EmployerForm.salary)
async def process_emp_salary(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ Введите сумму цифрами:")
        return
    await state.update_data(salary=int(message.text))
    await message.answer("📅 **Шаг 7 из 10:** Укажите График работы:")
    await state.set_state(EmployerForm.schedule)

@anketa_router.message(EmployerForm.schedule)
async def process_emp_sched(message: Message, state: FSMContext):
    await state.update_data(schedule=message.text)
    await message.answer("📍 **Шаг 8 из 10:** Укажите точный Адрес работы:")
    await state.set_state(EmployerForm.address)

@anketa_router.message(EmployerForm.address)
async def process_emp_addr(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    await message.answer("👤 **Шаг 9 из 10:** Укажите Контактное лицо:")
    await state.set_state(EmployerForm.contact_person)

@anketa_router.message(EmployerForm.contact_person)
async def process_emp_person(message: Message, state: FSMContext):
    await state.update_data(contact_person=message.text)
    await message.answer("📞 **Шаг 10 из 10:** Введите контактный Телефон компании:")
    await state.set_state(EmployerForm.phone)

@anketa_router.message(EmployerForm.phone)
async def preview_employer_form(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    data = await state.get_data()
    
    preview_text = (
        f"🏁 **Проверьте данные вашей вакансии:**\n\n"
        f"🏢 Компания: {data['company_name']}\n"
        f"🏙 Город: {data['city']}\n"
        f"💼 Должность: {data['position']}\n"
        f"💵 Зарплата: {data['salary']} тг\n"
        f"📅 График: {data['schedule']}\n"
        f"📍 Адрес: {data['address']}\n"
        f"📞 Контакт: {data['contact_person']} ({data['phone']})"
    )
    # Біз оны FSM-де сақтауға жібереміз, бірақ кейін рөлді де өзгертеміз
    await state.update_data(form_type="vacancy")
    await message.answer(preview_text, reply_markup=get_confirm_keyboard(), parse_mode="Markdown")


@anketa_router.callback_query(F.data == "confirm_save")
async def save_data_to_db(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Мәліметтерді базаға жазу және сәйкестендіруді (Matching) іске қосу"""
    data = await state.get_data()
    user_db = await get_or_create_user(callback.from_user.id)
    
    async with AsyncSessionLocal() as session:
        if data.get("form_type") == "vacancy":
            # Вакансияны сақтау (ТЗ 3.2)
            new_vacancy = Vacancy(
                employer_id=user_db.id, company_name=data['company_name'], city=data['city'],
                position=data['position'], requirements=data['requirements'], conditions=data['conditions'],
                salary=data['salary'], schedule=data['schedule'], address=data['address'],
                contact_person=data['contact_person'], phone=data['phone']
            )
            session.add(new_vacancy)
            await session.commit()
            await session.refresh(new_vacancy)
            
            await callback.message.answer("🎉 **Вакансия добавлена!**\nМы автоматически подбираем подходящих кандидатов.", parse_mode="Markdown")
            # Сәйкес келетін анкеттерді автоматты іздеуді бастау
            await check_matching_for_vacancy(new_vacancy, bot)
            
        else:
            # ТЗ 2.2: Кандидатты сақтау логикасы (Ескі кодқа SQLAlchemy жазу нұсқасы)
            new_resume = Resume(
                user_id=user_db.id, name=data.get('name', 'Пользователь'), age=data.get('age', 18),
                city=data.get('city', 'Алматы'), position=data.get('position', 'Повар'),
                experience=data.get('experience', 0), prev_jobs=data.get('prev_jobs', '-'),
                schedule=data.get('schedule', '2/2'), salary=data.get('salary', 0), contact=data.get('contact', '-')
            )
            session.add(new_resume)
            await session.commit()
            await callback.message.answer("🎉 **Анкета успешно сохранена!**", reply_markup=get_payment_keyboard())

    await callback.message.edit_reply_markup(reply_markup=None)
    await state.clear()


@anketa_router.callback_query(F.data == "confirm_save")
async def save_data_to_db(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """ТЗ 2.2 & 3.2: Деректерді PostgreSQL-ге асинхронды контекстте жазу"""
    data = await state.get_data()
    user_db = await get_or_create_user(callback.from_user.id, callback.from_user.username)
    
    async with AsyncSessionLocal() as session:
        async with session.begin():
            if data.get("form_type") == "vacancy":
                # Рольді жаңарту
                await session.execute(
                    update(User).where(User.id == user_db.id).values(role=UserRole.EMPLOYER)
                )
                
                new_vacancy = Vacancy(
                    employer_id=user_db.id, company_name=data['company_name'], city=data['city'],
                    position=data['position'], requirements=data['requirements'], conditions=data['conditions'],
                    salary=data['salary'], schedule=data['schedule'], address=data['address'],
                    contact_person=data['contact_person'], phone=data['phone']
                )
                session.add(new_vacancy)
                # Контекст аяқталғанда commit автоматты түрде орындалады (session.begin арқасында)
                
                await callback.message.answer("🎉 **Вакансия добавлена!**\nМы автоматически подбираем подходящих кандидатов.", parse_mode="Markdown")
                # Матчингті іске қосу (бұл асинхронды функция ішінде жаңа сессия ашады)
                asyncio.create_task(check_matching_for_vacancy(new_vacancy, bot))
                
            else:
                # Рольді жаңарту
                await session.execute(
                    update(User).where(User.id == user_db.id).values(role=UserRole.CANDIDATE)
                )
                
                new_resume = Resume(
                    user_id=user_db.id, name=data.get('name'), age=data.get('age'),
                    city=data.get('city'), position=data.get('position'),
                    experience=data.get('experience'), prev_jobs=data.get('prev_jobs'),
                    schedule=data.get('schedule'), salary=data.get('salary'), contact=data.get('contact')
                )
                session.add(new_resume)
                
                await callback.message.answer("🎉 **Анкета успешно сохранена!**", reply_markup=get_payment_keyboard())

    await callback.message.edit_reply_markup(reply_markup=None)
    await state.clear()