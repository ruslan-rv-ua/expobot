from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from services.bot import BotsManager

router = APIRouter(prefix="")
# TODO: fix this when pytest supports this
# router.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def show_bots(request: Request):
    return templates.TemplateResponse(
        "bots.html",
        {
            "request": request,
        },
    )


@router.get("/partial", response_class=HTMLResponse)
async def bots_table_tbody(request: Request, bots_manager: BotsManager = Depends()):
    bots = await bots_manager.get_bots()

    return templates.TemplateResponse(
        "partial/bots_table_tbody.html", {"request": request, "bots": bots}
    )

@router.get("/{id}", response_class=HTMLResponse)
async def show_bot(request: Request, bots_manager: BotsManager = Depends()):
    bot = await bots_manager.get_bot_with_details()

    return templates.TemplateResponse(
        "bot.html", {"request": request, "bot": bot}
    )

@router.get("/partial/status/{id}", response_class=HTMLResponse)
async def bot_status(request: Request, bots_manager: BotsManager = Depends()):
    bot = await bots_manager.get_bot_with_details()

    return templates.TemplateResponse(
        "partial/bot_status.html", {"request": request, "bot": bot}
    )