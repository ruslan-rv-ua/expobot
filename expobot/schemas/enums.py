import enum


class BotStatus(str, enum.Enum):
    """Bot status."""

    RUNNING = "running"
    STOPPED = "stopped"

    def __str__(self) -> str:
        return self.value

class OrderSide(str, enum.Enum):
    """Order side."""

    BUY = "buy"
    SELL = "sell"

class OrderStatus(str, enum.Enum):
    """Order status."""
    
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    