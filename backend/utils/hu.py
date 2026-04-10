from collections import Counter
#Counter是Python标准库collections模块中的一个类，用于计数可哈希对象的出现次数。在这个代码中，Counter被用来统计麻将牌的数量，以便判断是否满足特定的和牌条件。

HONOR_ORDER = {
    "east": 1,
    "south": 2,
    "west": 3,
    "north": 4,
    "white": 5,
    "green": 6,
    "red": 7,
}

#_tile_sort_key函数为每张牌生成一个排序键，先根据牌的类型排序，再根据牌的数字排序。这样可以确保在判断和牌时，牌的顺序是一致的。
def _tile_sort_key(tile: str) -> tuple[int, int]:
    if _is_suit(tile):
        suit_rank = {"m": 1, "s": 2, "p": 3}[tile[0]]
        num_rank = int(tile[1])
        return (suit_rank, num_rank)
    return (9, HONOR_ORDER.get(tile, 99))

#is_seven_pairs函数检查给定的14张牌是否满足七对的和牌条件，即必须有7种不同的牌，每种牌恰好出现两次。
def _is_suit(tile: str) -> bool:
    return len(tile) == 2 and tile[0] in {"m", "p", "s"} and tile[1].isdigit()


def _remove_sequence(counter: Counter, suit: str, n: int) -> bool:
    a = f"{suit}{n}"
    b = f"{suit}{n+1}"
    c = f"{suit}{n+2}"
    if counter[a] and counter[b] and counter[c]:
        counter[a] -= 1
        counter[b] -= 1
        counter[c] -= 1
        return True
    return False

#核心算法
def _all_melds(counter: Counter) -> bool:
    #结束条件
    if sum(counter.values()) == 0: 
        return True


    remaining = [t for t, cnt in counter.items() if cnt > 0]
    tile = min(remaining, key=_tile_sort_key) if remaining else None
    if tile is None:
        return True

    # 先尝试刻子
    if counter[tile] >= 3:
        counter[tile] -= 3
        if _all_melds(counter):
            return True
        counter[tile] += 3

    # 再尝试顺子
    if _is_suit(tile):
        suit = tile[0]
        n = int(tile[1])
        if n <= 7 and _remove_sequence(counter, suit, n):
            if _all_melds(counter):
                return True
            # 回溯
            counter[f"{suit}{n}"] += 1
            counter[f"{suit}{n+1}"] += 1
            counter[f"{suit}{n+2}"] += 1

    return False

#TERMINAL_OR_HONOR_TILES包含所有的幺九牌和字牌，用于判断十三幺牌型
TERMINAL_OR_HONOR_TILES = {
    "m1",
    "m9",
    "s1",
    "s9",
    "p1",
    "p9",
    "east",
    "south",
    "west",
    "north",
    "white",
    "green",
    "red",
}

#七对
def is_seven_pairs(tiles14: list[str]) -> bool:
    if len(tiles14) != 14:
        return False
    counter = Counter(tiles14)
    return len(counter) == 7 and all(cnt == 2 for cnt in counter.values())

#十三幺
def is_thirteen_orphans(tiles14: list[str]) -> bool:
    if len(tiles14) != 14:
        return False
    counter = Counter(tiles14)

    # Must contain all 13 terminal/honor tiles at least once.
    if set(counter.keys()) - TERMINAL_OR_HONOR_TILES:
        return False
    if not TERMINAL_OR_HONOR_TILES.issubset(set(counter.keys())):
        return False

    # Exactly one of them appears twice and all others once.
    pair_count = 0
    for tile in TERMINAL_OR_HONOR_TILES:
        cnt = counter.get(tile, 0)
        if cnt == 2:
            pair_count += 1
        elif cnt != 1:
            return False
    return pair_count == 1

#普通和牌
def is_common_four_melds_one_pair(tiles14: list[str]) -> bool:
    if len(tiles14) != 14:
        return False

    counter = Counter(tiles14)
    for tile, cnt in list(counter.items()):
        if cnt >= 2:
            counter[tile] -= 2
            if _all_melds(counter.copy()):
                return True
            counter[tile] += 2
    return False


def is_standard_win(tiles14: list[str]) -> bool:
    # Keep public function name for compatibility with existing service calls,
    # while supporting a few common special winning patterns.
    return (
        is_common_four_melds_one_pair(tiles14)
        or is_seven_pairs(tiles14)
        or is_thirteen_orphans(tiles14)
    )