from tortoise import fields, models
from schemas.enums import OrderSide, OrderStatus


class Order(models.Model):
    id = fields.CharField(pk=True, max_length=100)
    datetime = fields.DatetimeField(auto_now_add=True)
    status = fields.CharEnumField(OrderStatus)
    side = fields.CharEnumField(OrderSide)
    symbol = fields.CharField(max_length=25, null=False)
    price = fields.FloatField(
        null=True,
        description="float price in quote currency (may be empty for market orders)",
    )
    average = fields.FloatField(description="float average filling price")
    amount = fields.FloatField(description="ordered amount of base currency")
    cost = fields.FloatField(description="total cost of order in quote currency")
    fee_currency = fields.CharField(max_length=10, description="fee currency")
    fee_coust = fields.FloatField(description="the fee amount in fee currency")
    fee_rate = fields.FloatField(null=True, description="the fee rate (if available)")

    bot = fields.ForeignKeyField(
        "my_app.bot", related_name="orders", on_delete=fields.CASCADE
    )

    class Meta:
        table = "orders"

    def __str__(self):
        return f"ORM Order: {self.id}"
