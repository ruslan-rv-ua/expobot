from fastapi import APIRouter, Depends, Response, status
from services.runner import BotRunner, get_bot_runner
from models.bot import BotStatus, BotWithDetails, BotCreate
from services.bot import BotsManager
from models.bot import Bot

router = APIRouter(
    prefix="/bots",
    tags=["bots"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Bot not found"}},
)


@router.get("/", response_model=list[Bot])
async def get_bots(
    status: BotStatus | None = None, bots_manager: BotsManager = Depends()
) -> list[Bot]:
    """Get all bots"""
    return await bots_manager.get_bots(status)


@router.get("/{bot_id}", response_model=BotWithDetails)
async def get_bot(bots_manager: BotsManager = Depends()):
    """Get bot by id"""
    return await bots_manager.get_bot_with_details()


@router.post("/", response_model=Bot)
async def create_bot(bot_data: BotCreate, bots_manager: BotsManager = Depends()):
    """Create bot"""
    return await bots_manager.create_bot(bot_data)


@router.delete(
    "/{bot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_bot(bots_manager: BotsManager = Depends()) -> Response:
    """Delete bot by id"""
    await bots_manager.delete_bot()
    return Response(status_code=status.HTTP_204_NO_CONTENT)  # TODO: fix this


@router.get("/{bot_id}/tick", status_code=status.HTTP_200_OK)
async def tick(
    last_price: float | None = None, bot_runner: BotRunner = Depends(get_bot_runner)
):
    """Tick"""
    await bot_runner.tick(last_price)
    return Response(status_code=status.HTTP_200_OK)
