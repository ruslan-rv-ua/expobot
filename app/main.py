"""
TODO:
    - move logger to class
    - backtesting
    - statistics
    - start/stop
    - change `Exception` to own exceptions
    - level 0 price
    - GUI for bot:
        - refactor files structure
        - bots list view
            - remove 'description' column
            - add 'message' column
            - add 'account/exchange' column
            - add 'symbol' column
        - start/stop bot
        - bot view
        - add bot
        - delete bot
    - make descriptions, examples, status codes more clear
"""

import logging

from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every

from . import config, routers
from .services.db import init_db
from .services.tick import tick

__VERSION__ = "0.0.1"


logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
logger.setLevel(logging.ERROR)

app = FastAPI(
    title="ExpoBot",
    description="""Expobot API\n\n
Trade cryptocurrencies in a simple manner.\n\n
## Features:\n
TODO""",
    version=__VERSION__,
)


app.include_router(routers.bot.router, prefix="/api")
app.include_router(routers.gui.router)


@app.on_event("startup")
def startup():
    init_db()


# TODO: move to services/bot.py?
APP_ON = True
APP_ON = False


@app.on_event("startup")
@repeat_every(seconds=config.TICK_PERIOD, raise_exceptions=True)
def tick_periodic_task():
    global APP_ON
    if APP_ON:
        tick()


if __name__ == "__main__":
    pass
