from fastapi import APIRouter, Depends, Response, status

from ..models.bot import Bot, BotCreate, BotStatus, BotWithDetails
from ..api.bot import BotsManager
from ..services.bot import BotRunner, get_bot_runner

router = APIRouter(
    prefix="/bots",
    tags=["bots"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Bot not found"}},
)


@router.get("/", response_model=list[Bot])
def get_bots(
    status: BotStatus | None = None, bots_manager: BotsManager = Depends()
) -> list[Bot]:
    """Get all bots"""
    return bots_manager.get_bots(status)


@router.get("/{bot_id}", response_model=BotWithDetails)
def get_bot(bots_manager: BotsManager = Depends()):
    """Get bot by id"""
    return bots_manager.get_bot_with_details()


@router.post("/", response_model=Bot)
def create_bot(bot_data: BotCreate, bots_manager: BotsManager = Depends()):
    """Create bot"""
    return bots_manager.create_bot(bot_data)


@router.delete(
    "/{bot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_bot(bots_manager: BotsManager = Depends()) -> Response:
    """Delete bot by id"""
    bots_manager.delete_bot()
    return Response(status_code=status.HTTP_204_NO_CONTENT)  # TODO: fix this


@router.get("/{bot_id}/tick", status_code=status.HTTP_200_OK)
def tick(bot_runner: BotRunner = Depends(get_bot_runner)):
    """Tick"""
    bot_runner.tick()
    return Response(status_code=status.HTTP_200_OK)


@router.get("/{bot_id}/run", status_code=status.HTTP_200_OK)
def run_bot(bot_runner: BotRunner = Depends(get_bot_runner)):
    """Run bot"""
    bot_runner.run()
    return Response(status_code=status.HTTP_200_OK)


@router.get("/{bot_id}/stop", status_code=status.HTTP_200_OK)
def stop_bot(bot_runner: BotRunner = Depends(get_bot_runner)):
    """Stop bot"""
    bot_runner.stop()
    return Response(status_code=status.HTTP_200_OK)
