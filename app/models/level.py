import enum
from sqlmodel import Field, Relationship, select, SQLModel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.bot import BotModel


class LevelStatus(str, enum.Enum):
    """Level status."""

    NONE = "none"
    OPEN = "open"
    CLOSED = "closed"

    def __str__(self) -> str:
        return self.value


class LevelBase(SQLModel):
    """Level base."""

    floor: int = Field(index=True)
    price: float
    amount: float | None = None
    buy_status: LevelStatus = Field(default=LevelStatus.NONE)
    buy_order_id: str | None = Field(default=None, index=True)
    sell_status: LevelStatus = Field(default=LevelStatus.NONE)
    sell_order_id: str | None = Field(default=None, index=True)

    bot_id: int = Field(foreign_key="bots.id")

    def is_empty(self) -> bool:
        """Check if level is empty."""
        return (
            self.buy_status == LevelStatus.NONE and self.sell_status == LevelStatus.NONE
        )

    def side(self) -> str:
        match self.buy_status, self.sell_status:
            case (LevelStatus.NONE, LevelStatus.NONE):
                return None
            case (LevelStatus.OPEN, LevelStatus.NONE):
                return 'buy'
            case (LevelStatus.NONE, LevelStatus.OPEN):
                return 'sell'
        return ''
            

    def __repr__(self) -> str:
        return f"[{self.floor} {self.buy_status}-{self.sell_status} {self.amount}x {self.price}]"

    


class LevelModel(LevelBase, table=True):
    """Database model for Level"""

    __tablename__ = "levels"

    id: int | None = Field(default=None, primary_key=True)

    bot: "BotModel" = Relationship(back_populates="levels")


class Level(LevelBase):
    """Schema for Level"""

    id: int
