from fastapi import APIRouter, Depends, Path, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from models.order import OrderSide, OrderStatus
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


@router.get("/{bot_id}", response_class=HTMLResponse)
async def show_bot(request: Request, bot_id: str):
    return templates.TemplateResponse(
        "bot.html", {"request": request, "bot_id": bot_id}
    )


@router.get("/partial/{bot_id}", response_class=HTMLResponse)
async def bot_details(request: Request, bots_manager: BotsManager = Depends()):
    bot = await bots_manager.get_bot_with_details()
    base, quote = bot.symbol.split("/")
    closed_orders = [
        order for order in bot.orders if order.status == OrderStatus.CLOSED
    ]
    buy_orders = [order for order in closed_orders if order.side == OrderSide.BUY]
    sell_orders = [order for order in closed_orders if order.side == OrderSide.SELL]
    base_bought = sum(order.amount for order in buy_orders)
    base_sold = sum(order.amount for order in sell_orders)
    base_balance = base_bought - base_sold
    quote_outcome = sum(order.cost for order in buy_orders)
    quote_income = sum(order.cost for order in sell_orders)
    quote_balance = quote_income - quote_outcome
    profit = quote_balance + base_balance * bot.last_price
    profit_percent = round(profit / quote_balance * 100, 2)
    stats = dict(
        base=base,
        quote=quote,
        base_balance=base_balance,
        quote_balance=quote_balance,
        quote_balance_at_last_price=profit,
        profit=profit,
        profit_percent=profit_percent,
    )

    return templates.TemplateResponse(
        "partial/bot_details.html",
        {"request": request, "bot": bot, "stats": stats},
    )
