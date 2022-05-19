import enum
from datetime import datetime
from typing import TYPE_CHECKING
from sqlmodel import Relationship, SQLModel, Field

if TYPE_CHECKING:
    from models.bot import BotModel


class OrderSide(str, enum.Enum):
    """Order side."""

    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, enum.Enum):
    """Order status."""

    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class OrderBase(SQLModel):
    order_id: str
    timestamp: int = Field(default=datetime.utcnow().timestamp())
    status: OrderStatus
    side: OrderSide
    symbol: str = Field(min_length=1, max_length=21)
    price: float = Field(
        description="float price in quote currency (may be empty for market orders)"
    )
    average: float | None = Field(description="float average filling price")
    amount: float = Field(description="ordered amount of base currency")
    cost: float = Field(description="total cost of order in quote currency")
    fee_currency: str = Field(max_length=10, description="fee currency")
    fee_cost: float = Field(description="the fee amount in fee currency")
    fee_rate: float | None = Field(
        default=None, description="the fee rate (if available)"
    )

    bot_id: int = Field(foreign_key="bots.id")


class OrderModel(OrderBase, table=True):
    """Database model for orders"""

    __tablename__ = "orders"

    id: int | None = Field(default=None, primary_key=True)

    bot: "BotModel" = Relationship(back_populates="orders")


class Order(OrderBase):
    """Schema for order"""

    id: int
