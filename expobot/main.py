"""
TODO:
    - move all constants from models to settings
    - make descriptions and examples for models
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from tortoise.contrib.fastapi import register_tortoise
from routers.bot import bot_router


import settings
from services.exchange import exchanges

app = FastAPI(
    title="ExpoBot",
    description="""Expobot API\n\n
Trade cryptocurrencies in a simple manner.\n\n
## Features:\n
TODO""",
    version=settings.VERSION,
)

app.include_router(bot_router)

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
