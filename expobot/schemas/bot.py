from datetime import datetime
import pydantic
import settings
from schemas.enums import BotStatus


class BotBase(pydantic.BaseModel):
    """Base model for bot."""

    name: str
    description: str | None = None
    exchange_account: str = pydantic.Field(
        ...,
        min_length=1,
        max_length=255,
        description="Exchange account id.",
        example="binance_main_account",
    )
    symbol: str = pydantic.Field(
        ...,
        min_length=1,
        max_length=25,
        description="Symbol.",
        example="BTC/USDT",
    )
    amount: float = pydantic.Field(
        default=1.0,
        description="Amount of asset to trade.",
        example=0.01,
    )
    buy_up_levels: int = pydantic.Field(
        default=settings.DEFAULT_BUY_UP_LEVELS,
        description="How much buy orders to place above current level.",
        example=settings.DEFAULT_BUY_UP_LEVELS,
    )
    buy_down_levels: int = pydantic.Field(
        default=settings.DEFAULT_BUY_DOWN_LEVELS,
        description="How much buy orders to place below current level.",
        example=settings.DEFAULT_BUY_DOWN_LEVELS,
    )


class Bot(BotBase):
    """Bot schema."""

    id: int
    status: BotStatus

    level_height: float
    taker: float = pydantic.Field(..., description="Taker fee rate, 0.002 = 0.2%")
    maker: float = pydantic.Field(..., description="Maker fee rate, 0.0015 = 0.15%")
    total_level_height: float
    level_0_price: float = pydantic.Field(
        ...,
        description="Price of level 0 at startup.",
        example=1.2345,
    )
    current_level: int
    current_price: float
    current_price_timestamp: int

    created_at: datetime
    updated_at: datetime
    message: str | None = None

    class Config:
        orm_mode = True


class BotCreate(BotBase):
    level_percent: float = pydantic.Field(
        default=settings.DEFAULT_LEVEL_PERCENT,
        description="Level height in percent.",
        example=settings.DEFAULT_LEVEL_PERCENT,
    )
