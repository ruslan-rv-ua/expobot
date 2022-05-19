import enum
from datetime import datetime
from models.level import Level

import settings
from sqlmodel import Field, Relationship, SQLModel

from models.order import Order, OrderModel


class BotStatus(str, enum.Enum):
    """Bot status."""

    RUNNING = "running"
    STOPPED = "stopped"

    def __str__(self) -> str:
        return self.value


class BotData(SQLModel):
    created_at: datetime = Field(default=datetime.now())

    # parameters
    name: str = Field(min_length=1, max_length=100)
    exchange_account: str = Field(min_length=1, max_length=255)
    symbol: str = Field(min_length=1, max_length=21)
    level_height: float
    trade_amount: float
    level_0_price: float
    buy_up_levels: int
    buy_down_levels: int

    # calculated
    taker: float
    maker: float
    total_level_height: float

    # state
    status: BotStatus
    last_price: float
    last_level: int


class BotModel(BotData, table=True):
    """Database model for Bot"""

    __tablename__ = "bots"

    id: int | None = Field(default=None, primary_key=True)

    orders: list[OrderModel] = Relationship(back_populates="bot")


class Bot(BotData):
    """Schema for Bot"""

    id: int


class BotWithDetails(Bot):
    """Schema for Bot with orders and levels"""

    # TODO: add levels
    orders: list[Order]
    levels: list[Level]


class BotCreate(SQLModel):
    """Schema for Bot creation"""

    name: str = Field(min_length=1, max_length=100)
    exchange_account: str = Field(min_length=1, max_length=255)
    symbol: str = Field(min_length=1, max_length=21)
    level_height: float = Field(default=settings.DEFAULT_LEVEL_HEIGHT)
    trade_amount: float = Field(default=settings.DEFAULT_TRADE_AMOUNT)
    level_0_price: float = Field(default=settings.DEFAULT_LEVEL_0_PRICE)  # TODO: remove
    buy_up_levels: int = Field(default=settings.DEFAULT_BUY_UP_LEVELS)
    buy_down_levels: int = Field(default=settings.DEFAULT_BUY_DOWN_LEVELS)

    class Config:
        schema_extra = {
            "example": {
                "name": "Bot 1",
                "description": "Bot 1 description",
                "exchange_account": "binance_main_account",
                "symbol": "BTC/USDT",
                "level_height": settings.DEFAULT_LEVEL_HEIGHT,
                "trade_amount": settings.DEFAULT_TRADE_AMOUNT,
                "level_0_price": settings.DEFAULT_LEVEL_0_PRICE,
                "buy_up_levels": settings.DEFAULT_BUY_UP_LEVELS,
                "buy_down_levels": settings.DEFAULT_BUY_DOWN_LEVELS,
            }
        }
