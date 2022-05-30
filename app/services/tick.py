from sqlmodel import select

from ..models.bot import BotModel
from .db import get_session
from .bot import get_bot_runner


def tick():
    session = get_session()
    bot_ids = session.exec(select(BotModel.id)).all()
    for bot_id in bot_ids:
        bot_runner = get_bot_runner(bot_id)
        bot_runner.tick()
