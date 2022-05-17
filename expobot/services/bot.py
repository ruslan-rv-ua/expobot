from fastapi import HTTPException
from schemas.enums import BotStatus
from models.bot import BotModel
from schemas.bot import Bot, BotCreate
from services.exchange import exchanges_manager


class BotService:
    def __init__(self, id: int):
        self.id = id
        # TODO: fix this: self.exchange = exchanges[self.bot.exchange_account]

    async def __get(self) -> BotModel:
        """Get bot by id"""
        bot_orm = await BotModel.get_or_none(id=self.id)
        if bot_orm is None:
            raise HTTPException(status_code=404, detail="Bot not found")
        return bot_orm

    @staticmethod
    async def get_bots(status: BotStatus | None = None) -> list[Bot]:
        """Get all bot ids"""
        if status is None:
            bots_orm = await BotModel.all()
        else:
            bots_orm = await BotModel.filter(status=status)
        return [Bot.from_orm(bot_orm) for bot_orm in bots_orm]

    async def get_bot(self) -> Bot:
        """Get bot by id"""
        return Bot.from_orm(await self.__get())

    @staticmethod
    async def create_bot(bot_data: BotCreate) -> Bot:
        """Create bot"""

        if await BotModel.get_or_none(name=bot_data.name) is not None:
            raise HTTPException(
                status_code=409, detail="Bot with the same name already exists"
            )
        if (
            await BotModel.get_or_none(
                exchange_account=bot_data.exchange_account, symbol=bot_data.symbol
            )
            is not None
        ):
            raise HTTPException(
                status_code=409,
                detail="Bot with the same exchange account and symbol already exists",
            )
        exchange = exchanges_manager[bot_data.exchange_account]
        symbol_info = exchange.fetch_symbol_info(bot_data.symbol)
        taker = symbol_info["taker"]
        maker = symbol_info["maker"]
        level_height = bot_data.level_percent / 100
        total_level_height=level_height + taker + maker
        bot_orm = await BotModel.create(
            **bot_data.dict(exclude_unset=True),
            status=BotStatus.STOPPED,
            taker=taker,
            maker=maker,
            level_height=level_height,
            total_level_height=total_level_height,
            level_0_price=111,#!!!
            current_level=0,
            current_price=0,
            current_price_timestamp=0,
        )
        return Bot.from_orm(bot_orm)

    async def delete_bot(self) -> None:
        """Delete bot by id"""
        bot_orm = await self.__get()
        await bot_orm.delete()
