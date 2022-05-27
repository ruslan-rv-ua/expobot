import enum
from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel

from .. import config
from .level import Level
from .order import Order, OrderModel


class BotStatus(str, enum.Enum):
    """Bot status."""

    RUNNING = "running"
    STOPPED = "stopped"

    def __str__(self) -> str:
        return self.value


class BotData(SQLModel):
    created_at: datetime = Field(default=datetime.now())

    # parameters
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
    message: str | None = None
    message_datetime: datetime | None = None
    last_price: float
    last_floor: int

    def __str__(self) -> str:
        return (
            f"#{self.id} {self.symbol} @ {self.exchange_account}"
        )

    def __repr__(self) -> str:
        return f"<BotModel {self.id} {self.symbol} {self.status} @ {self.exchange_account}>"


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

    exchange_account: str = Field(min_length=1, max_length=255)
    symbol: str = Field(min_length=1, max_length=21)
    level_height: float
    trade_amount: float = Field(default=config.DEFAULT_TRADE_AMOUNT)
    level_0_price: float = Field(default=config.DEFAULT_LEVEL_0_PRICE)  # TODO: remove
    buy_up_levels: int = Field(default=config.DEFAULT_BUY_UP_LEVELS)
    buy_down_levels: int = Field(default=config.DEFAULT_BUY_DOWN_LEVELS)

    class Config:
        schema_extra = {
            "example": {
                "name": "Bot 1",
                "description": "Bot 1 description",
                "exchange_account": "binance_main_account",
                "symbol": "BTC/USDT",
                "level_height": config.DEFAULT_LEVEL_HEIGHT,
                "trade_amount": config.DEFAULT_TRADE_AMOUNT,
                "level_0_price": config.DEFAULT_LEVEL_0_PRICE,
                "buy_up_levels": config.DEFAULT_BUY_UP_LEVELS,
                "buy_down_levels": config.DEFAULT_BUY_DOWN_LEVELS,
            }
        }
