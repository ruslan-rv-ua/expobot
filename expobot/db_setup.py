from sqlmodel import Session, SQLModel, create_engine

from models.bot import BotCreate, BotModel
from models.order import OrderModel

DATABASE_URL = f"sqlite:///./expobot/database_expobot.db"
engine = create_engine(DATABASE_URL)

SQLModel.metadata.drop_all(engine)
SQLModel.metadata.create_all(engine)


def create_bot():
    with Session(engine) as session:
        bot_data = BotCreate(
            name="test", description="test", exchange_account="fkuna", symbol="TRX/UAAH"
        )
        bot = BotModel(
            **bot_data.dict(),
            status="stopped",
            taker=0.0025,
            maker=0.0025,
            total_level_height=0.01,
            last_level=0,
            last_price=0,
        )
        session.add(bot)
        session.commit()
        session.refresh(bot)
        return bot


def create_order(bot_id: int):
    with Session(engine) as session:
        order = OrderModel(
            bot_id=bot_id,
            symbol="TRX/UAAH",
            side="buy",
            price=12.5,
            amount=1,
            status="open",
            cost=12.5,
            fee_currency="TRX",
            fee_cost=0.01,
            fee_rate=0.01,
        )
        session.add(order)
        session.commit()
        session.refresh(order)
        return order


if __name__ == "__main__":
    bot = create_bot()
    order = create_order(bot.id)
