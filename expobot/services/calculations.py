import math


def floor_to_price(floor: int, level_height: float, level_0_price: float) -> float:
    """
    Calculates the price of a level
    :param level: level to calculate the price for
    :param level_0_price: price of level 0
    :return: price of the level
    """
    return level_0_price * level_height**floor


def price_to_floor(price: float, level_height: float, level_0_price: float) -> int:
    """
    Calculates the level of a price
    :param price: price to calculate the level for
    :param level_0_price: price of level 0
    :return: level of the price
    """
    return round(math.log(price / level_0_price, level_height))


# TODO: remove this function
# def price_to_level(price: float, level_height: float) -> int:
#     return int(math.log(price, level_height))
# def level_to_price(level: int, level_height: float) -> float:
#     return level_height**level
