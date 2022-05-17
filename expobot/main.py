"""
TODO:
    - move all constants from models to settings
    - make descriptions, examples, status codes more clear
"""

from fastapi import APIRouter, FastAPI
from db import init_db, get_session
import settings
from routers.bot import router as bot_router
# from routers.gui import router as gui_router

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
# app.include_router(gui_router)


@app.on_event("startup")
async def startup():
    await init_db()


if __name__ == "__main__":
    pass
