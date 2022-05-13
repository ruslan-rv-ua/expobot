from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from models.bot import BotModel
from schemas.bot import Bot
from services.bot import BotService

router = APIRouter(prefix="")
router.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def show_bots(request: Request):
    bots = await BotService.get_bots()

    return templates.TemplateResponse(
        "show_bots.html", {"request": request, "bots": bots}
    )
