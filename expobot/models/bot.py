from datetime import datetime
from schemas.enums import BotStatus
import settings
from sqlmodel import SQLModel, Field


class BotBase(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(
        default=None, min_length=1, max_length=255
    )
    exchange_account: str = Field(min_length=1, max_length=255)
    symbol: str = Field(min_length=1, max_length=21)
    trade_amount: float = 1.0
    level_height: float = Field(default=settings.DEFAULT_LEVEL_HEIGHT)
    level_0_price: float = Field(default=settings.DEFAULT_LEVEL_0_PRICE)
    buy_up_levels: int = Field(default=settings.DEFAULT_BUY_UP_LEVELS)
    buy_down_levels: int = Field(default=settings.DEFAULT_BUY_DOWN_LEVELS)


class Bot(BotBase, table=True):
    """Database model for Bot"""

    id: int = Field(primary_key=True)
    status: BotStatus

    taker: float
    maker: float
    total_level_height: float

    last_price: float
    last_level: int

    created_at: datetime = Field(default=datetime.now())
