from sqlmodel import Session, SQLModel, create_engine, select
from models.level import LevelModel

from models.bot import BotCreate, BotModel
from models.order import OrderModel

import requests

DATABASE_URL = f"sqlite:///./expobot/database_expobot.db"
engine = create_engine(DATABASE_URL)

# SQLModel.metadata.drop_all(engine)
# SQLModel.metadata.create_all(engine)


def delete_all_bots():
    with Session(engine) as session:
        bots = session.exec(select(BotModel)).all()
        for bot in bots:
            session.delete(bot)
        session.commit()

def delete_all_orders():
    with Session(engine) as session:
        orders = session.exec(select(OrderModel)).all()
        for order in orders:
            session.delete(order)
        session.commit()

def delete_all_levels():
    with Session(engine) as session:
        levels = session.exec(select(LevelModel)).all()
        for level in levels:
            session.delete(level)
        session.commit()


def create_bot():
    bot_data = BotCreate(
        name="Bina DOT", exchange_account="binance_main_account", symbol="DOT/USDT", level_height=1
    )
    response = requests.post("http://localhost:8000/api/bots", json=bot_data.dict())
    return response.json()


# def create_bot():
#     with Session(engine) as session:
#         bot_data = BotCreate(
#             name="test", description="test", exchange_account="fkuna", symbol="TRX/UAH"
#         )
#         bot = BotModel(
#             **bot_data.dict(),
#             status="stopped",
#             taker=0.0025,
#             maker=0.0025,
#             total_level_height=0.01,
#             last_floor=0,
#             last_price=0,
#         )
#         session.add(bot)
#         session.commit()
#         session.refresh(bot)
#         return bot


def create_order(bot_id: int):
    with Session(engine) as session:
        order = OrderModel(
            bot_id=bot_id,
            order_id="test",
            symbol="TRX/UAH",
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
    # delete_all_bots()
    delete_all_orders()
    delete_all_levels()
    # bot = create_bot()
    # print(bot)
    # order = create_order(bot.id)
