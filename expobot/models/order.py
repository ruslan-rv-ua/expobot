from datetime import datetime
from schemas.enums import OrderSide, OrderStatus
from sqlmodel import ForeignKey, SQLModel, Field

class Order(SQLModel, table=True):
    id: int | None = None
    datetime: datetime
    status: OrderStatus
    side: OrderSide
    symbol: str = Field(min_length=1, max_length=10)
    price: float = Field(description="float price in quote currency (may be empty for market orders)")
    average:float = Field(description="float average filling price")
    amount:float = Field(description="ordered amount of base currency")
    cost:float = Field(description="total cost of order in quote currency")
    fee_currency:str = Field(max_length=10, description="fee currency")
    fee_coust:float = Field(description="the fee amount in fee currency")
    fee_rate:float|None = Field(default=None, description="the fee rate (if available)")

    bot_id = ForeignKey('Bot', related_name='orders')

