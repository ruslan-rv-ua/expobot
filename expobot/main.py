"""
TODO:
    - separate exchange class into 2 classes:
        - exchange class for real exchanges
        - exchange class for virtual exchanges
    - place_order_* in services/exchange.py
    - cancel_order_* in services/exchange.py
    - fetch orders in services/exchange.py
    - bot's trading logic in services/bot.py
    - tick() in services/bot.py
    - GUI for bot:
        - bots list view
            - remove 'description' column
            - add 'message' column
            - add 'account/exchange' column
            - add 'symbol' column
        - start/stop bot
        - bot view
        - add bot
        - delete bot
    - go exchange async
    - make descriptions, examples, status codes more clear
"""

from fastapi import APIRouter, FastAPI
from fastapi_utils.tasks import repeat_every

import settings
from routers.bot import router as bot_router
from routers.gui import router as gui_router
from services.db import init_db
from services.tick import tick

app = FastAPI(
    title="ExpoBot",
    description="""Expobot API\n\n
Trade cryptocurrencies in a simple manner.\n\n
## Features:\n
TODO""",
    version=settings.VERSION,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(bot_router)

app.include_router(api_router)
app.include_router(gui_router)


@app.on_event("startup")
async def startup():
    await init_db()

# @app.on_event("startup")
# @repeat_every(seconds=settings.TICK_PERIOD, raise_exceptions=True)
# async def tick_periodic_task():
#     print('----- tick_periodic_task -----')
#     await tick()


if __name__ == "__main__":
    pass
