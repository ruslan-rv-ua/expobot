from fastapi import HTTPException
from schemas.enums import BotStatus
from models.bot import BotModel
from schemas.bot import Bot, BotCreate, Bots
from services.exchange import exchanges_manager


class BotService:
    def __init__(self, id: str):
        self.id = id
        # print(Bot.from_orm(self.bot))
        # TODO: fix this: self.exchange = exchanges[self.bot.exchange_account]

    async def __get(self) -> BotModel:
        """Get bot by id"""
        bot_orm = await BotModel.get_or_none(id=self.id)
        if bot_orm is None:
            raise HTTPException(status_code=404, detail="Bot not found")
        return bot_orm

    @staticmethod
    async def get_bots(status: BotStatus | None) -> Bots:
        """Get all bot ids"""
        if status is None:
            bots_orm = await BotModel.all()
        else:
            bots_orm = await BotModel.filter(status=status)
        return Bots.from_orm(bots_orm)

    async def get_bot(self) -> Bot:
        """Get bot by id"""
        return Bot.from_orm(await self.__get())

    async def create_bot(self, bot_data: BotCreate) -> Bot:
        """Create bot"""
        if await BotModel.get_or_none(id=self.id) is not None:
            raise HTTPException(status_code=409, detail="Bot already exists")
        exchange = exchanges_manager[bot_data.exchange_account]
        symbol_info = exchange.fetch_symbol_info(bot_data.symbol)
        taker = symbol_info["taker"]
        maker = symbol_info["maker"]
        level_height = bot_data.level_percent / 100
        bot_orm = await BotModel.create(
            id=self.id,
            description=bot_data.description,
            status=BotStatus.STOPPED,
            exchange_account=bot_data.exchange_account,
            symbol=bot_data.symbol,
            buy_up_levels=bot_data.buy_up_levels,
            buy_down_levels=bot_data.buy_down_levels,
            level_height=level_height,
            taker=taker,
            maker=maker,
            total_level_height=level_height + taker + maker,
        )
        return Bot.from_orm(bot_orm)

    async def delete_bot(self) -> None:
        """Delete bot by id"""
        bot_orm = await self.__get()
        await bot_orm.delete()
