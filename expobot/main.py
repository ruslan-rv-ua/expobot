"""
TODO:
    - move all constants from models to settings
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from tortoise.contrib.fastapi import register_tortoise

import settings
from models.base import Message
from models.bot import BotIn, BotOut, DBBot

from services.exchange import exchanges
app = FastAPI(
    title="ExpoBot",
    description="""Expobot API\n\n
Trade cryptocurrencies in a simple manner.\n\n
## Features:\n
TODO""",
    version=settings.VERSION,
)


@app.get("/bots/", response_model=list[BotOut])
async def get_bots():
    db_bots = await DBBot.all()
    return [BotOut.from_orm(db_bot) for db_bot in db_bots]


@app.get("/bots/{name}", response_model=BotOut, responses={404: {"model": Message}})
async def get_bot(name: str):
    db_bot = await DBBot.get_or_none(name=name)
    if db_bot is None:
        return JSONResponse(
            status_code=404,
            content={"message": f"Bot with name `{name}` does not exist"},
        )
    response = BotOut.from_orm(db_bot)
    return response


@app.post("/bots", response_model=BotOut, responses={409: {"model": Message}})
async def create_bot(bot: BotIn):
    """Create a VERY NICE bot. TODO: Add description."""
    if await DBBot.filter(name=bot.name).exists():
        return JSONResponse(
            status_code=409,
            content={"message": f"Bot with name `{bot.name}` already exists."},
        )
    if bot.exchange_account not in settings.EXCHANGE_ACCOUNTS:
        return JSONResponse(
            status_code=409,
            content={
                "message": f"Exchange account `{bot.exchange_account}` does not exist."
            },
        )
    exchange = exchanges[bot.exchange_account]
    symbol_info = exchange.fetch_symbol_info(bot.symbol)
    if symbol_info is None:
        return JSONResponse(
            status_code=409,
            content={
                "message": f"Symbol `{bot.symbol}` is not supported on exchange `{bot.exchange_account}`."
            },
        )
    taker = symbol_info["taker"]
    maker = symbol_info["maker"]
    print(f'>>>>> TAKER: {taker} | MAKER: {maker}')
    level_height = bot.level_percent / 100
    total_level_height = level_height + taker + maker
    db_bot = await DBBot.create(
        **bot.dict(),
        level_height=level_height,
        taker=taker,
        maker=maker,
        total_level_height=total_level_height,
    )
    return BotOut.from_orm(db_bot)


register_tortoise(
    app,
    db_url=settings.DATABASE_URL,
    modules={"models": ["models.bot"]},
    generate_schemas=settings.GENERATE_SCHEMAS,
)


if __name__ == "__main__":
    from services.exchange import exchanges

    ex = exchanges["fake_kuna"]
    print(ex.fetch_symbol_info("XRP/UAH"))
