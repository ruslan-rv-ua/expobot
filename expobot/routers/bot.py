from fastapi import APIRouter, Depends, Response, status
from schemas.bot import Bot, BotCreate
from schemas.enums import BotStatus
from services.bot import BotService

router = APIRouter(
    prefix="/bots",
    tags=["bots"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Bot not found"}},
)


@router.get("/", response_model=list[Bot])
async def get_bots(status: BotStatus | None = None) -> list[Bot]:
    """Get all bots"""
    return await BotService.get_bots(status=status)


@router.get("/{id}", response_model=Bot)
async def get_bot(bot_service: BotService = Depends(BotService)):
    """Get bot by id"""
    return await bot_service.get_bot()


@router.post("/", response_model=Bot)
async def create_bot(bot_data: BotCreate):
    """Create bot"""
    return await BotService.create_bot(bot_data)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_bot(bot_service: BotService = Depends(BotService)) -> Response:
    """Delete bot by id"""
    await bot_service.delete_bot()
    return Response(status_code=status.HTTP_204_NO_CONTENT)  # TODO: fix this
