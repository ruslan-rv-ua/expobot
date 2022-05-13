"""Trade Session Schema"""
from pydantic import BaseModel, Field
from schemas.enums import SessionStatus

class SessionBase(BaseModel):
    """Base model for session."""

    id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Session id.",
        example="session_binance_btc_usdt",
    )
    status: SessionStatus
    description: str | None = None
    created_at: str
    updated_at: str
    closed_at: str
    level_0_price: float
    current_level: int
    current_price: float