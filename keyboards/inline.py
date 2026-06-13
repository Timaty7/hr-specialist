"""
Жобаның барлық интерактивті батырмалары. Төлем және рефералка қосылды.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍🍳 Ищу работу", callback_data="role_candidate")],
        [InlineKeyboardButton(text="💼 Ищу сотрудника", callback_data="role_employer")]
    ])

def get_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить и Сохранить", callback_data="confirm_save")]
    ])

def get_matching_keyboard(vacancy_id: int) -> InlineKeyboardMarkup:
    """ТЗ 4.1: Кандидатқа вакансия ұсынылғандағы Да/Нет батырмалары"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, хочу", callback_data=f"match_yes_{vacancy_id}"),
            InlineKeyboardButton(text="❌ Нет", callback_data=f"match_no_{vacancy_id}")
        ]
    ])

def get_payment_keyboard() -> InlineKeyboardMarkup:
    """ТЗ 10.6: Төлем жасау сілтемесін беретін батырмалар"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить подписку", callback_data="pay_now")],
        [InlineKeyboardButton(text="🎁 Пригласить друга", callback_data="invite_friend")]
    ])