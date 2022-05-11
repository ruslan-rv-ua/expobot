"""Trade Session Model"""

from tortoise import fields, models

from schemas.enums import BotStatus
from .bot import BotModel


class TradeSession(models.Model):
    """Trade Session Model"""

    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    closed_at = fields.DatetimeField(null=True)

    bot = fields.OneToOneField(
        BotModel, related_name="session", on_delete=fields.SET_NULL, null=True
    )

    class Meta:
        table = "trade_sessions"

    def __str__(self):
        return f"[{self.id}]"

    def is_active(self) -> bool:
        return self.bot is not None and self.bot.status != BotStatus.STOPPED
