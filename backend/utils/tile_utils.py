import random

#创建牌的列表
def build_tiles() -> list[str]:
    tiles = []
    suits = ["m", "s", "p"] #msp,万嗦饼
    for suit in suits:
        for n in range(1, 10):
            tiles.extend([f"{suit}{n}"] * 4)#extend方法将每种牌添加4次，表示四张相同的牌

    honors = ["east", "south", "west", "north", "white", "green", "red"]
    for h in honors:
        tiles.extend([h] * 4)
    return tiles

#洗牌
def shuffle_tiles(tiles: list[str]) -> list[str]:
    copied = tiles[:]#创建牌的副本，以免修改原始列表
    random.shuffle(copied)
    return copied