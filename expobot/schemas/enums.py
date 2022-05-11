import enum


class BotStatus(str, enum.Enum):
    """Bot status."""

    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"

class OrderSide(str, enum.Enum):
    """Order side."""

    BUY = "buy"
    SELL = "sell"

class OrderStatus(str, enum.Enum):
    """Order status."""
    
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    