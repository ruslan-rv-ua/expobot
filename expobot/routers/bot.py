from fastapi import APIRouter, Depends, HTTPException
from urllib3 import HTTPResponse
from models.bot import BotModel

from schemas.bot import Bot, BotCreate
from services.bot import BotService

router = APIRouter(prefix="/bots")


@router.get("/", response_model=list[str], tags=["bots"])
async def get_all_bot_ids():
    """Get all bot ids"""
    # bot_ids = await BotModel.all().values_list("id", flat=True)
    # return bot_ids
    return await BotService.get_bot_ids()


@router.get("/{id}", response_model=Bot, tags=["bots"])
async def get_bot(bot_service: BotService = Depends(BotService)):
    """Get bot by id"""
    return await bot_service.get_bot()

@router.delete("/{id}", tags=["bots"])
async def delete_bot(bot_service: BotService = Depends(BotService)):
    """Delete bot by id"""
    # await bot_service.delete()
    print('xxx'*200)
    return '111'*200

# async def get_bot(id: str):
#     '''
#     '''
#     db_bot = await BotModel.get_or_none(id=id)
#     if db_bot is None:
#         raise HTTPException(status_code=404, detail="Bot not found")
#     response = Bot.from_orm(db_bot)
#     return response


# @bot_router.post("/bots", response_model=BotOut, responses={409: {"model": Message}})
# async def create_bot(bot: BotIn):
#     """Create a VERY NICE bot. TODO: Add description."""
#     if await BotModel.filter(name=bot.name).exists():
#         return JSONResponse(
#             status_code=409,
#             content={"message": f"Bot with name `{bot.name}` already exists."},
#         )
#     if bot.exchange_account not in settings.EXCHANGE_ACCOUNTS:
#         return JSONResponse(
#             status_code=409,
#             content={
#                 "message": f"Exchange account `{bot.exchange_account}` does not exist."
#             },
#         )
#     exchange = exchanges[bot.exchange_account]
#     symbol_info = exchange.fetch_symbol_info(bot.symbol)
#     if symbol_info is None:
#         return JSONResponse(
#             status_code=409,
#             content={
#                 "message": f"Symbol `{bot.symbol}` is not supported on exchange `{bot.exchange_account}`."
#             },
#         )
#     taker = symbol_info["taker"]
#     maker = symbol_info["maker"]
#     print(f">>>>> TAKER: {taker} | MAKER: {maker}")
#     level_height = bot.level_percent / 100
#     total_level_height = level_height + taker + maker
#     db_bot = await BotModel.create(
#         **bot.dict(),
#         level_height=level_height,
#         taker=taker,
#         maker=maker,
#         total_level_height=total_level_height,
#     )
#     return BotOut.from_orm(db_bot)
