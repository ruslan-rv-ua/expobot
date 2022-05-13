"""Trade Session Model"""

from tortoise import fields, models

from schemas.enums import BotStatus


class TradeSession(models.Model):
    """Trade Session Model"""

    id = fields.CharField(max_length=255, pk=True)
    status = fields.CharEnumField(BotStatus)
    description = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    closed_at = fields.DatetimeField(null=True)
    level_0_price = fields.FloatField()
    current_level = fields.IntField()
    current_price = fields.FloatField()

    bot = fields.OneToOneField(
        model_name="BotModel",
        related_name="session",
        on_delete=fields.SET_NULL,
        null=True,
    )

    class Meta:
        table = "sessions"

    def __str__(self):
        return f"[{self.}]"

