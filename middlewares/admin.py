"""
Creator Қауіпсіздік Сүзгісі (Middleware).
Бұл фильтр арқылы өтетін командаларды тек .env-де жазылған Creator ғана баса алады.
"""
from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from config.settings import settings

class CreatorOnlyMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id

        # Егер жазған адам .env-дегі Криатор болса ғана өткізеді
        if user_id == settings.CREATOR_ID:
            return await handler(event, data)
        
        # Басқа пайдаланушылар үшін бұл хендлерлер мүлдем жабық болады (жауап бермейді)
        return