"""
TODO:
    - level 0 price
    - tiemstamp for last update
    - backtesting
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


# TODO: move to services/bot.py?
APP_ON = True
# APP_ON = False

@app.on_event("startup")
@repeat_every(seconds=settings.TICK_PERIOD, raise_exceptions=True)
async def tick_periodic_task():
    global APP_ON
    if not APP_ON:
        return
    await tick()


if __name__ == "__main__":
    pass
