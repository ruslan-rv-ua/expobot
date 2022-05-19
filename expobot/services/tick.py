from datetime import datetime

from .bot import BotRunner, BotsManager
from .db import async_session_class
from .exchange import exchanges_manager

def get_nonce():
    return int(datetime.now().timestamp() * 1000)


async def tick():
    async with async_session_class() as session:
        exchanges_manager.clear_all_caches()
        bots_data = await BotsManager(session).get_bots()
        nonce=get_nonce()
        for bot_data in bots_data:
            print("1111 " * 10)
            bot_runner = BotRunner(bot_data.id, session=session)
            await bot_runner.tick(nonce)
            print("3333 " * 10)
