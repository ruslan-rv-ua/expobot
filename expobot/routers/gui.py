from fastapi import APIRouter, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from models.bot import BotModel

from schemas.bot import Bot
router = APIRouter(prefix="/gui")
router.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def show_bots(request: Request):
    # db_bots = await BotModel.all().values_list()
    db_bots = await BotModel.all().values()
    # bots = [Bot.from_orm(bot) for bot in db_bots]
    bots = db_bots

    return templates.TemplateResponse(
        "show_bots.html", {"request": request, "bots": bots}
    )
