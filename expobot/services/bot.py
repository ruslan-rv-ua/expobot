from fastapi import HTTPException
from models.bot import BotModel
from schemas.bot import Bot
from services.exchange import exchanges

class BotService:
    def __init__(self, id: str):
        self.id = id
        # print(Bot.from_orm(self.bot))
        # TODO: fix this: self.exchange = exchanges[self.bot.exchange_account]
            

    async def __get(self) -> BotModel:
        """Get bot by id"""
        bot = await BotModel.get_or_none(id=self.id)
        if bot is None:
            raise HTTPException(status_code=404, detail="Bot not found")
        return bot

    @staticmethod
    async def get_bot_ids() -> list[str]:
        """Get all bot ids"""
        return await BotModel.all().values_list("id", flat=True)

    async def get(self) -> Bot:
        """Get bot by id"""
        return Bot.from_orm(await self.__get())