from tortoise import fields, models
from schemas.enums import BotStatus


class BotBaseModel(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=50, unique=True)
    description = fields.TextField(null=True)
    status = fields.CharEnumField(BotStatus)
    exchange_account = fields.CharField(max_length=255, null=False)
    symbol = fields.CharField(max_length=25, null=False)
    amount = fields.FloatField(null=False)
    buy_up_levels = fields.IntField()
    buy_down_levels = fields.IntField()

    level_height = fields.FloatField(null=False)
    taker = fields.FloatField(null=False)
    maker = fields.FloatField(null=False)
    total_level_height = fields.FloatField()

    level_0_price = fields.FloatField()

    class Meta:
        abstract = True


class BotModel(BotBaseModel):

    current_level = fields.IntField()
    current_price = fields.FloatField()
    current_price_timestamp = fields.IntField()

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    message = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "bots"

    def __str__(self):
        return f"ORM BotModel: {self.name}"


class BotArchiveModel(BotBaseModel):
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "bots_archive"

    def __str__(self):
        return f"ORM BotArchiveModel: {self.name}"
