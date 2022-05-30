from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..api.bot import BotsManager
from ..models.order import OrderSide, OrderStatus

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(prefix="")


@router.get("/", response_class=HTMLResponse)
def bots_list(request: Request):
    return templates.TemplateResponse(
        "bots/bots_list.html",
        {
            "request": request,
        },
    )


@router.get("/bots/bots_table_tbody", response_class=HTMLResponse)
def bots_table_tbody(request: Request, bots_manager: BotsManager = Depends()):
    bots = bots_manager.get_bots()
    return templates.TemplateResponse(
        "bots/bots_table_tbody.html", {"request": request, "bots": bots}
    )


@router.get("/bot/{bot_id}", response_class=HTMLResponse)
def bot_page(request: Request, bot_id: str):
    return templates.TemplateResponse(
        "bot/bot.html", {"request": request, "bot_id": bot_id}
    )


@router.get("/bot/{bot_id}/details", response_class=HTMLResponse)
def bot_details(request: Request, bots_manager: BotsManager = Depends()):
    bot = bots_manager.get_bot_with_details()
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
    # profit_percent = round(profit / quote_balance * 100, 2) # TODO: !!! fix
    stats = dict(
        base=base,
        quote=quote,
        base_balance=base_balance,
        quote_balance=quote_balance,
        quote_balance_at_last_price=profit,
        profit=profit,
        # profit_percent=profit_percent,
    )
    return templates.TemplateResponse(
        "bot/bot_details.html",
        {"request": request, "bot": bot, "stats": stats},
    )
