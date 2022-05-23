from models.bot import BotModel
from sqlmodel import select

from .db import Session
from .runner import get_bot_runner


async def tick():
    query = select(BotModel.id)
    async with Session() as session:
        result = await session.execute(query)
    for bot_id in result.scalars():
        bot_runner = await get_bot_runner(bot_id)
        await bot_runner.tick()
