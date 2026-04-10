from backend.utils.hu import is_standard_win


def test_standard_win_detects_triplets_and_sequence_mix():
    # Pair: s1 s1
    # Triplets: m5 m5 m5, m7 m7 m7, p2 p2 p2
    # Sequence: s6 s7 s8
    hand = [
        "s1",
        "m7",
        "m5",
        "s7",
        "p2",
        "p2",
        "p2",
        "m5",
        "s1",
        "s6",
        "m7",
        "m7",
        "s8",
        "m5",
    ]
    assert is_standard_win(hand) is True


def test_standard_win_detects_seven_pairs():
    hand = [
        "m1",
        "m1",
        "m2",
        "m2",
        "s3",
        "s3",
        "s4",
        "s4",
        "p5",
        "p5",
        "p6",
        "p6",
        "east",
        "east",
    ]
    assert is_standard_win(hand) is True
