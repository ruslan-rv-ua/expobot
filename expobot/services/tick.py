from datetime import datetime


from .bot import BotsManager
from .runner import BotRunner
from .db import Session
from .exchange import exchanges_manager


# TODO: remove this
def get_nonce():
    return int(datetime.now().timestamp() * 1000)


async def tick():
    exchanges_manager.clear_all_caches()
    async with Session() as session:
        bots_data = await BotsManager(session=session).get_bots()
    nonce = get_nonce()
    for bot_data in bots_data:
        exchange = exchanges_manager[bot_data.exchange_account]
        bot_runner = BotRunner(bot_data=bot_data, exchange=exchange)
        await bot_runner.tick(nonce)
