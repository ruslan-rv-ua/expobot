import requests
from sqlmodel import Session, create_engine, select

from app.models.bot import BotCreate, BotModel
from app.models.level import LevelModel
from app.models.order import OrderModel

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
    print("All bots deleted")


def delete_all_orders():
    with Session(engine) as session:
        orders = session.exec(select(OrderModel)).all()
        for order in orders:
            session.delete(order)
        session.commit()
    print("All orders deleted")


def delete_all_levels():
    with Session(engine) as session:
        levels = session.exec(select(LevelModel)).all()
        for level in levels:
            session.delete(level)
        session.commit()
    print("All levels deleted")


def create_bot(
    *, exchange_account: str, symbol: str, level_height: float = 0.01
):
    bot_data = BotCreate(
        exchange_account=exchange_account,
        symbol=symbol,
        level_height=level_height,
    )
    response = requests.post("http://localhost:8000/api/bots", json=bot_data.dict())
    print(f"Bot created:", response)


if __name__ == "__main__":
    # delete_all_bots()
    # delete_all_orders()
    # delete_all_levels()
    # bot = create_bot(exchange_account="Backtest Binance", symbol="DOT/USDT", level_height=0.01)
    create_bot(exchange_account="VirtaBina", symbol="BTC/USDT", level_height=0.008)
    create_bot(exchange_account="Virtual Kuna", symbol="TRX/USDT", level_height=0.005)
