import enum


class BotStatus(str, enum.Enum):
    """Bot status."""

    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"

    def __str__(self) -> str:
        return self.value

class SessionStatus(str, enum.Enum):
    """Session status."""

    OPEN = "open"
    CLOSED = "closed"

class OrderSide(str, enum.Enum):
    """Order side."""

    BUY = "buy"
    SELL = "sell"

class OrderStatus(str, enum.Enum):
    """Order status."""
    
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    