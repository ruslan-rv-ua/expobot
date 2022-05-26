import enum
from sqlmodel import Field, Relationship, select, SQLModel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.bot import BotModel


class LevelStatus(str, enum.Enum):
    """Level status."""

    OPEN = "open"
    CLOSED = "closed"
    NONE = "none"

    def __str__(self) -> str:
        return self.value


class LevelBase(SQLModel):
    """Level base."""

    floor: int = Field(index=True)
    price: float
    buy_order_id: str | None = Field(default=None, index=True)
    buy_amount: float | None = None
    buy_status: LevelStatus = Field(default=LevelStatus.NONE)
    sell_order_id: str | None = Field(default=None, index=True)
    sell_amount: float | None = None
    sell_status: LevelStatus = Field(default=LevelStatus.NONE)

    bot_id: int = Field(foreign_key="bots.id")

    def __str__(self) -> str:
        b = f"{self.buy_status}" if self.buy_status != "none" else "-"
        s = f"{self.sell_status}" if self.sell_status != "none" else "-"
        return f"[{self.floor} {b} {s}]"

    def is_empty(self) -> bool:
        return (
            self.buy_status == LevelStatus.NONE and self.sell_status == LevelStatus.NONE
        )



class LevelModel(LevelBase, table=True):
    """Database model for Level"""

    __tablename__ = "levels"

    id: int | None = Field(default=None, primary_key=True)

    bot: "BotModel" = Relationship(back_populates="levels")

    def set_buy_order(self, order_id: str, amount: float):
        self.buy_order_id = order_id
        self.buy_amount = amount
        self.buy_status = LevelStatus.OPEN

    def set_sell_order(self, order_id: str, amount: float):
        self.sell_order_id = order_id
        self.sell_amount = amount
        self.sell_status = LevelStatus.OPEN

    def clear_buy_order(self) -> None:
        self.buy_order_id = None
        self.buy_amount = None
        self.buy_status = LevelStatus.NONE

    def clear_sell_order(self) -> None:
        self.sell_order_id = None
        self.sell_amount = None
        self.sell_status = LevelStatus.NONE



class Level(LevelBase):
    """Schema for Level"""

    id: int
