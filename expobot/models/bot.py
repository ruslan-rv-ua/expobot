import enum
import pydantic
from tortoise import fields, models


DEFAULT_LEVEL_HEIGHT_PERCENT = 3
DEFAULT_BUY_UP_LEVELS = 3
DEFAULT_BUY_DOWN_LEVELS = 3


class BOT_STATUS(str, enum.Enum):
    """Bot status."""

    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class DBBot(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, unique=True)
    description = fields.TextField(null=True)
    status = fields.CharEnumField(BOT_STATUS, default=BOT_STATUS.READY)
    exchange_account = fields.CharField(max_length=255, null=False)
    symbol = fields.CharField(max_length=25, null=False)
    buy_up_levels = fields.IntField()
    buy_down_levels = fields.IntField()

    level_height = fields.FloatField(default=DEFAULT_LEVEL_HEIGHT_PERCENT)
    taker = fields.FloatField(null=False)
    maker = fields.FloatField(null=False)
    total_level_height = fields.FloatField()

    class Meta:
        table = "bots"

    def __str__(self):
        return f"[{self.status}] {self.name}"


class BotOut(pydantic.BaseModel):
    name: str
    description: str | None = None
    status: BOT_STATUS
    exchange_account: str
    symbol: str
    buy_up_levels: int
    buy_down_levels: int

    level_height: float
    taker: float = pydantic.Field(..., description="Taker fee rate, 0.002 = 0.2%")
    maker: float = pydantic.Field(..., description="Maker fee rate, 0.0015 = 0.15%")
    total_level_height: float

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "name": "bot_name",
                "description": "bot description",
                "status": "ready",
                "exchange_account": "binance_main_account",
                "symbol": "BTC/USDT",
                "buy_up_levels": 3,
                "buy_down_levels": 3,
                "level_height": 0.03,
                "taker": 0.002,
                "maker": 0.0018,
                "total_level_height": 0.0338,
            }
        }


class BotIn(pydantic.BaseModel):
    name: str
    description: str | None = None
    exchange_account: str
    symbol: str
    level_percent: float = DEFAULT_LEVEL_HEIGHT_PERCENT
    buy_up_levels: int = DEFAULT_BUY_UP_LEVELS
    buy_down_levels: int = DEFAULT_BUY_DOWN_LEVELS

    class Config:
        schema_extra = {
            "example": {
                "name": "bot_binance_btc_usdt",
                "description": "This is a bot",
                "exchange_account": "binance_main_account",
                "symbol": "BTC/USDT",
                "level_percent": 3,
                "buy_up_levels": 3,
                "buy_down_levels": 3,
            }
        }
