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


class Bot(BotBase):
    """Bot schema."""

    id: int
    status: BotStatus
    buy_up_levels: int
    buy_down_levels: int

    level_height: float
    taker: float = pydantic.Field(..., description="Taker fee rate, 0.002 = 0.2%")
    maker: float = pydantic.Field(..., description="Maker fee rate, 0.0015 = 0.15%")
    total_level_height: float

    class Config:
        orm_mode = True


class BotCreate(BotBase):
    level_percent: float = pydantic.Field(
        default=settings.DEFAULT_LEVEL_PERCENT,
        description="Level height in percent.",
        example=settings.DEFAULT_LEVEL_PERCENT,
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
