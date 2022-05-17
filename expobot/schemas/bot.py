from models.bot import Bot, BotBase


class BotCreate(BotBase):
    """Schema for creating a Bot"""

    id: int | None = None

    class Config:
        schema_extra = {
            "example": {
                "name": "Bot 1",
                "exchange_account": "fake_kuna",
                "symbol": "TRX/UAH",
                "level_height": 0.01,
            }
        }


class BotRead(Bot):
    """Schema for reading a Bot"""

    pass


class BotReadWithDetails(BotRead):
    """Schema for reading a Bot with orders and levels"""

    # TODO: add orders and levels
    pass
