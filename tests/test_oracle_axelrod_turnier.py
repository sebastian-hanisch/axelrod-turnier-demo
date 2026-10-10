"""Orakel-Tests axelrod-turnier-demo: der Kern wird gegen UNABHÄNGIGE Rechenwege geprüft (DEMO-PLAYBOOK §12, ORACLE-PLAYBOOK §2).

1. Erwartete Auszahlung zweier REAKTIVER Strategien (Aktion hängt nur von der letzten Aktion des Gegners ab) unter Rauschen: exakt per
   Verteilung über die Zustände (letzte Aktionen beider), gegen den Mittelwert vieler simulierter Spiele.
2. Deterministische Strategien ohne Rauschen: Zustandsautomaten, hier unabhängig und anders aufgeschrieben, gegen die Simulation (exakt).
3. Invariante: ohne Rauschen erzielt Tit-for-Tat gegen KEINEN Gegner mehr als der Gegner (Spiegeln, Beweis per Abzählen der Differenz).
4. Teilfeld-Stichprobe gegen Vollaufzählung aller Teilfelder auf einem kleinen Feld."""

import itertools
import random

import pytest

import axt_algorithm as A
import axt_constants as C
from axt_scenario import CLASSES, make, stage_payoff

# Reaktive Strategien: Wahrscheinlichkeit zu defektieren (erste Runde, nach Kooperation des Gegners, nach Defektion des Gegners)
REACTIVE = {
    "ALLC": (0.0, 0.0, 0.0),
    "ALLD": (1.0, 1.0, 1.0),
    "TFT": (0.0, 0.0, 1.0),
    "STFT": (1.0, 0.0, 1.0),
    "JOSS": (0.0, 0.1, 1.0),
    "PROBER": (0.0, 0.1, 1.0),
    "GTFT": (0.0, 0.0, 2 / 3),
    "RANDOM": (0.5, 0.5, 0.5),
    "BULLY": (1.0, 1.0, 0.0),
}


def exact_reactive(pa, pb, eps, rounds):
    """Erwartete mittlere Auszahlung je Runde (a, b) durch Fortschreiben der Verteilung über (letzte Aktion a, letzte Aktion b)."""
    def executed(p):                      # P(ausgeführte Aktion = D) bei Absicht D mit Wahrscheinlichkeit p
        return (1 - eps) * p + eps * (1 - p)

    qa, qb = executed(pa[0]), executed(pb[0])
    dist = {(x, y): (qa if x else 1 - qa) * (qb if y else 1 - qb) for x in (0, 1) for y in (0, 1)}
    tot_a = sum(p * stage_payoff(x, y) for (x, y), p in dist.items())
    tot_b = sum(p * stage_payoff(y, x) for (x, y), p in dist.items())
    for _ in range(rounds - 1):
        new = {k: 0.0 for k in dist}
        for (x, y), p in dist.items():
            qa, qb = executed(pa[1 + y]), executed(pb[1 + x])
            for x2, y2 in itertools.product((0, 1), repeat=2):
                new[(x2, y2)] += p * (qa if x2 else 1 - qa) * (qb if y2 else 1 - qb)
        dist = new
        tot_a += sum(p * stage_payoff(x, y) for (x, y), p in dist.items())
        tot_b += sum(p * stage_payoff(y, x) for (x, y), p in dist.items())
    return tot_a / rounds, tot_b / rounds


@pytest.mark.parametrize("eps", [0.0, 0.05, 0.2])
def test_simulation_matches_the_exact_expectation_for_reactive_pairs(eps):
    pairs = [("TFT", "TFT"), ("TFT", "ALLD"), ("JOSS", "GTFT"), ("STFT", "TFT"), ("RANDOM", "BULLY"), ("PROBER", "ALLC")]
    rounds, reps = 40, 1500
    for ka, kb in pairs:
        exp_a, exp_b = exact_reactive(REACTIVE[ka], REACTIVE[kb], eps, rounds)
        rng = random.Random(77)
        sim = [A.play_match(make(ka), make(kb), rounds, eps, rng) for _ in range(reps)]
        got_a = sum(s[0] for s in sim) / reps
        got_b = sum(s[1] for s in sim) / reps
        assert got_a == pytest.approx(exp_a, abs=0.07), (ka, kb, eps)
        assert got_b == pytest.approx(exp_b, abs=0.07), (ka, kb, eps)


def test_exact_reactive_by_hand():
    # TFT gegen ALLD, 4 Runden, ohne Rauschen: TFT 0 + 1 + 1 + 1 = 3, ALLD 5 + 1 + 1 + 1 = 8
    a, b = exact_reactive(REACTIVE["TFT"], REACTIVE["ALLD"], 0.0, 4)
    assert a == pytest.approx(3 / 4) and b == pytest.approx(8 / 4)


# --- deterministische Automaten, anders aufgeschrieben als die Strategien selbst -----------------------------------------------------------

def ref_grim(opp_actions):
    out, triggered = [], False
    for y in opp_actions:
        out.append(1 if triggered else 0)
        triggered = triggered or y == 1
    return out


def ref_tf2t(opp_actions):
    out, run = [], 0
    for y in opp_actions:
        out.append(1 if run >= 2 else 0)
        run = run + 1 if y == 1 else 0
    return out


def ref_pavlov(opp_actions):
    out, mine = [], 0
    for y in opp_actions:
        out.append(mine)
        mine = mine if y == 0 else 1 - mine
    return out


def ref_hard_tft(opp_actions):
    out, prev2 = [], [0, 0]
    for y in opp_actions:
        out.append(1 if 1 in prev2 else 0)
        prev2 = [prev2[1], y]
    return out


def ref_davis(opp_actions):
    out, seen_defect = [], False
    for t, y in enumerate(opp_actions):
        out.append(1 if (t >= 10 and seen_defect) else 0)
        seen_defect = seen_defect or y == 1
    return out


@pytest.mark.parametrize("key,ref", [("GRIM", ref_grim), ("TF2T", ref_tf2t), ("PAVLOV", ref_pavlov), ("HARD_TFT", ref_hard_tft), ("DAVIS", ref_davis)])
def test_deterministic_strategies_match_reference_automata_on_random_opponent_sequences(key, ref):
    for seed in range(40):
        rng = random.Random(seed)
        opp = [rng.randint(0, 1) for _ in range(40)]
        s = make(key)
        s.reset()
        own, hist_opp, gen = [], [], random.Random(0)
        for y in opp:
            own.append(s.act(own, hist_opp, gen))
            hist_opp.append(y)
        assert own == ref(opp), (key, seed)


# --- Invariante: Tit-for-Tat gewinnt ohne Rauschen kein einziges Spiel -------------------------------------------------------------------

@pytest.mark.parametrize("rounds", [1, 2, 7, 50, 200])
def test_tft_never_scores_more_than_its_opponent_without_noise(rounds):
    for key in C.STRATEGY_KEYS:
        for seed in range(6):
            rng = random.Random(seed)
            tft, other = A.play_match(make("TFT"), make(key), rounds, 0.0, rng)
            assert tft <= other + 1e-12, (key, rounds, seed, tft, other)


def test_the_difference_of_a_tft_match_is_at_most_one_exploitation():
    """Die Punktdifferenz ist höchstens T − S = 5 Punkte über das ganze Spiel (die einzige Ausbeutung ist die erste Runde)."""
    for key in C.STRATEGY_KEYS:
        rng = random.Random(3)
        tft, other = A.play_match(make("TFT"), make(key), 200, 0.0, rng)
        assert (other - tft) * 200 <= (C.T - C.S) + 1e-9, key


# --- Teilfelder gegen Vollaufzählung ----------------------------------------------------------------------------------------------------

def test_subfield_distribution_matches_exhaustive_enumeration():
    keys = ["TFT", "ALLC", "ALLD", "GRIM", "GTFT", "BULLY"]
    mat = A.payoff_matrix([(k, (lambda k=k: make(k))) for k in keys], 40, 0.0, 1, 1)
    size = 3
    others = [i for i in range(len(keys)) if i != 0]
    ranks = []
    for combo in itertools.combinations(others, size - 1):
        members = list(combo) + [0]
        _, score = A.ranking(mat, members)
        ranks.append(A.tied_rank(score, 0))
    exact = {r: ranks.count(r) / len(ranks) for r in (1, 2, 3)}
    res = A.subfield_outcomes(mat, keys, "TFT", size, 6000, 11)
    for r in (1, 2, 3):
        got = res["ranks"].count(r) / len(res["ranks"])
        assert got == pytest.approx(exact[r], abs=0.03), r


def test_every_strategy_has_a_reactive_description_or_is_covered_elsewhere():
    """Welche der 16 der exakten Reaktiv-Rechnung unterliegen, welche den Automaten-Referenzen: zusammen alle 16."""
    automata = {"GRIM", "TF2T", "PAVLOV", "HARD_TFT", "DAVIS"}
    other = {"ALTERNATOR", "GRADUAL"}          # eigene Handrechnung in test_algorithm.py
    assert set(REACTIVE) | automata | other == set(CLASSES)
