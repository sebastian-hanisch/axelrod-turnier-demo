"""Mini-Instanz-Tests je Einheit (DEMO-PLAYBOOK §1b): alles von Hand gerechnet, Auszahlungen 5/3/1/0, ohne Rauschen wenn nicht anders gesagt."""

import random

import pytest

import axt_algorithm as A
import axt_constants as C
from axt_scenario import CLASSES, make, stage_payoff

COOP, DEF = C.COOPERATE, C.DEFECT


def actions(key: str, opp_actions: list[int]) -> list[int]:
    """Die Aktionen von `key` gegen eine feste Folge von Gegneraktionen."""
    s = make(key)
    s.reset()
    own: list[int] = []
    opp: list[int] = []
    rng = random.Random(1)
    for y in opp_actions:
        own.append(s.act(own, opp, rng))
        opp.append(y)
    return own


# --- Auszahlung und Rauschen ---------------------------------------------------------------------------------------------------------------

def test_stage_payoffs():
    assert stage_payoff(COOP, COOP) == 3 and stage_payoff(COOP, DEF) == 0
    assert stage_payoff(DEF, COOP) == 5 and stage_payoff(DEF, DEF) == 1


def test_flip_never_changes_without_noise_and_always_with_noise_one(rng):
    assert all(A.flip(a, 0.0, rng) == a for a in (0, 1) for _ in range(50))
    assert all(A.flip(a, 1.0, rng) == 1 - a for a in (0, 1) for _ in range(50))


def test_flip_rate_matches_the_noise(rng):
    n = 20000
    flips = sum(A.flip(COOP, 0.05, rng) for _ in range(n))
    assert flips / n == pytest.approx(0.05, abs=0.007)


# --- Strategien ----------------------------------------------------------------------------------------------------------------------------

def test_tft_mirrors_the_last_action():
    assert actions("TFT", [DEF, COOP, DEF, DEF]) == [COOP, DEF, COOP, DEF]


def test_suspicious_tft_starts_with_defection():
    assert actions("STFT", [COOP, COOP, DEF]) == [DEF, COOP, COOP]


def test_grim_defects_forever_after_the_first_defection():
    assert actions("GRIM", [COOP, DEF, COOP, COOP]) == [COOP, COOP, DEF, DEF]


def test_tf2t_needs_two_defections_in_a_row():
    assert actions("TF2T", [DEF, COOP, DEF, DEF, COOP]) == [COOP, COOP, COOP, COOP, DEF]


def test_hard_tft_remembers_two_rounds():
    assert actions("HARD_TFT", [DEF, COOP, COOP, COOP]) == [COOP, DEF, DEF, COOP]


def test_pavlov_stays_after_cooperation_and_shifts_after_defection():
    # eigene Aktion C, Gegner D -> wechseln auf D; D und Gegner D -> wechseln auf C; C und Gegner C -> bleiben
    assert actions("PAVLOV", [DEF, DEF, COOP, COOP]) == [COOP, DEF, COOP, COOP]


def test_alternator_and_bully():
    assert actions("ALTERNATOR", [COOP] * 4) == [COOP, DEF, COOP, DEF]
    assert actions("BULLY", [COOP, DEF, COOP]) == [DEF, DEF, COOP]


def test_davis_cooperates_ten_rounds_then_turns_grim():
    assert actions("DAVIS", [DEF] * 12) == [COOP] * 10 + [DEF, DEF]
    assert actions("DAVIS", [COOP] * 12) == [COOP] * 12


def test_gradual_punishes_n_times_then_calms_down_twice():
    # gegen Immer-Defektieren: C | D | C C | D D | C C | D D D | C
    assert actions("GRADUAL", [DEF] * 12) == [COOP, DEF, COOP, COOP, DEF, DEF, COOP, COOP, DEF, DEF, DEF, COOP]


def test_gradual_resets_its_state():
    s = make("GRADUAL")
    rng = random.Random(1)
    own, opp = [], []
    for y in [DEF] * 6:
        own.append(s.act(own, opp, rng))
        opp.append(y)
    s.reset()
    assert (s.count, s.punish, s.calm) == (0, 0, 0)


def test_joss_defects_about_ten_percent_after_cooperation(rng):
    s = make("JOSS")
    own, opp = [], []
    n = 20000
    for _ in range(n):
        own.append(s.act(own, opp, rng))
        opp.append(COOP)
    assert sum(own) / n == pytest.approx(0.1, abs=0.01)


def test_gtft_forgives_one_third_of_defections(rng):
    s = make("GTFT")
    n = 20000
    forgiven = sum(1 for _ in range(n) if s.act([COOP], [DEF], rng) == COOP)
    assert forgiven / n == pytest.approx(1 / 3, abs=0.012)


def test_all_sixteen_strategies_exist_and_have_labels():
    assert tuple(CLASSES) == C.STRATEGY_KEYS
    assert all(CLASSES[k].label != "?" and CLASSES[k].description for k in CLASSES)


# --- Spiel und Matrix ----------------------------------------------------------------------------------------------------------------------

def test_match_by_hand_tft_against_alld(rng):
    a, b = A.play_match(make("TFT"), make("ALLD"), 10, 0.0, rng)
    assert a == pytest.approx(0.9) and b == pytest.approx(1.4)       # (0 + 9·1)/10 ; (5 + 9·1)/10


def test_match_by_hand_tft_against_tft(rng):
    a, b = A.play_match(make("TFT"), make("TFT"), 10, 0.0, rng)
    assert a == b == pytest.approx(3.0)


def test_match_by_hand_grim_against_alternator(rng):
    # (C,C) (C,D) (D,C) (D,D): Grim 3+0+5+1 = 9, Abwechsler 3+5+0+1 = 9, je 4 Runden
    a, b = A.play_match(make("GRIM"), make("ALTERNATOR"), 4, 0.0, rng)
    assert a == pytest.approx(2.25) and b == pytest.approx(2.25)


def test_pair_seed_ignores_the_order_of_the_pair():
    assert A.pair_seed(5, "TFT", "ALLD") == A.pair_seed(5, "ALLD", "TFT")
    assert A.pair_seed(5, "TFT", "ALLD") != A.pair_seed(6, "TFT", "ALLD")
    assert A.pair_seed(5, "TFT", "ALLD") != A.pair_seed(5, "TFT", "ALLC")


def entries(keys):
    return [(k, (lambda k=k: make(k))) for k in keys]


def test_ranking_by_hand_for_three_strategies():
    mat = A.payoff_matrix(entries(["ALLC", "ALLD", "TFT"]), 10, 0.0, 1, 1)
    # ALLC: gegen ALLD 0, gegen TFT 3 ; ALLD: 5 und 1,4 ; TFT: 3 und 0,9
    assert mat[0][1] == 0.0 and mat[0][2] == 3.0 and mat[1][0] == 5.0
    assert mat[1][2] == pytest.approx(1.4) and mat[2][1] == pytest.approx(0.9)
    order, score = A.ranking(mat, [0, 1, 2])
    assert [["ALLC", "ALLD", "TFT"][i] for i in order] == ["ALLD", "TFT", "ALLC"]
    assert score[0] == pytest.approx(1.5) and score[1] == pytest.approx(3.2) and score[2] == pytest.approx(1.95)


def test_ranking_rejects_a_single_strategy():
    with pytest.raises(ValueError):
        A.ranking([[3.0]], [0])


def test_ranking_breaks_ties_by_index():
    mat = [[3.0, 3.0], [3.0, 3.0]]
    assert A.ranking(mat, [0, 1])[0] == [0, 1]


def test_tournament_over_a_subfield_is_a_submatrix_of_the_full_one():
    full_keys = ["ALLC", "ALLD", "TFT", "JOSS", "RANDOM", "GRADUAL"]
    full = A.payoff_matrix(entries(full_keys), 60, 0.02, 4, 9)
    sub_keys = ["RANDOM", "TFT", "JOSS"]                           # andere Reihenfolge, Teilmenge
    sub = A.payoff_matrix(entries(sub_keys), 60, 0.02, 4, 9)
    for i, ki in enumerate(sub_keys):
        for j, kj in enumerate(sub_keys):
            assert sub[i][j] == full[full_keys.index(ki)][full_keys.index(kj)], (ki, kj)


def test_matrix_is_reproducible_and_depends_on_the_seed():
    a = A.payoff_matrix(entries(["TFT", "JOSS", "RANDOM"]), 50, 0.01, 3, 1)
    b = A.payoff_matrix(entries(["TFT", "JOSS", "RANDOM"]), 50, 0.01, 3, 1)
    c = A.payoff_matrix(entries(["TFT", "JOSS", "RANDOM"]), 50, 0.01, 3, 2)
    assert a == b and a != c


def test_subfield_outcomes_validates_its_input():
    mat = [[3.0] * 4 for _ in range(4)]
    keys = ["A", "B", "C", "D"]
    with pytest.raises(ValueError):
        A.subfield_outcomes(mat, keys, "TFT", 3, 10, 1)
    with pytest.raises(ValueError):
        A.subfield_outcomes(mat, keys, "A", 9, 10, 1)


def test_subfield_outcomes_counts_add_up():
    keys = ["ALLC", "ALLD", "TFT", "GRIM", "TF2T"]
    mat = A.payoff_matrix(entries(keys), 30, 0.0, 1, 1)
    res = A.subfield_outcomes(mat, keys, "TFT", 3, 200, 4)
    assert len(res["ranks"]) == 200 and sum(res["winners"].values()) == pytest.approx(200.0)   # Gleichstände teilen den Sieg
    assert all(1 <= r <= 3 for r in res["ranks"])
