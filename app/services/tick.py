from sqlmodel import select, Session

from ..db import engine
from ..models.bot import BotModel
from .bot import get_bot_runner


def tick():
    with Session(engine) as session:
        bot_ids = session.exec(select(BotModel.id)).all()
    for bot_id in bot_ids:
        bot_runner = get_bot_runner(bot_id)
        bot_runner.tick()
