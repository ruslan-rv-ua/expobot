import math


def price_to_level(price: float, level_height: float) -> int:
    return int(math.log(price, level_height))


def level_to_price(level: int, level_height: float) -> float:
    return level_height**level
