from tortoise import fields, models
from schemas.enums import BotStatus


class BotModel(models.Model):
    id = fields.CharField(max_length=50, pk=True)
    description = fields.TextField(null=True)
    status = fields.CharEnumField(BotStatus)
    exchange_account = fields.CharField(max_length=255, null=False)
    symbol = fields.CharField(max_length=25, null=False)
    buy_up_levels = fields.IntField()
    buy_down_levels = fields.IntField()

    level_height = fields.FloatField(null=False)
    taker = fields.FloatField(null=False)
    maker = fields.FloatField(null=False)
    total_level_height = fields.FloatField()

    class Meta:
        table = "bots"

    def __str__(self):
        return f"[{self.status}] {self.id}"
