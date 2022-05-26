from asyncio.log import logger
from sqlmodel import select

from ..models.bot import BotModel
from .db import SessionLocal
from .bot import get_bot_runner


async def tick():
    async with SessionLocal() as session:
        result = await session.execute(select(BotModel.id))
    for bot_id in result.scalars():
        bot_runner = await get_bot_runner(bot_id)
        await bot_runner.tick()
