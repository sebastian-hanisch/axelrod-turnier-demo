"""Die trainierte Strategie: eine Tabelle über die letzten zwei Runden beider Spieler, per Hill-Climbing gegen ein Feld trainiert.

Idee nach Harper et al. (2017): eine Strategie ist ein Bitvektor; zufällige Bitwechsel bleiben, wenn die mittlere Auszahlung gegen die
Trainingsgegner nicht sinkt. Eigene, kleine Umsetzung; ausdrücklich KEIN Nachbau der dort trainierten Strategien."""

import json
import random
from pathlib import Path

import axt_constants as C
from axt_algorithm import play_match, Factory
from axt_scenario import Strategy, make

DATA_FILE = Path(__file__).resolve().parent / "axt_data.json"


class TableStrategy(Strategy):
    """Bits 0..15: Aktion je Kontext (eigene vorletzte, eigene letzte, Gegner vorletzte, Gegner letzte); Bit 16 und 17: Start- und zweiter Zug."""
    key, label, nice = C.TRAINED_KEY, "Trainierte Tabelle", False
    description = "Tabelle über die letzten zwei Runden beider Spieler, per Hill-Climbing gegen ein Feld trainiert."

    def __init__(self, bits):
        if len(bits) != C.TABLE_BITS:
            raise ValueError(f"{C.TABLE_BITS} Bits erwartet")
        self.bits = tuple(int(b) for b in bits)

    def act(self, own, opp, rng):
        n = len(own)
        if n == 0:
            return self.bits[16]
        if n == 1:
            return self.bits[17]
        return self.bits[own[-2] * 8 + own[-1] * 4 + opp[-2] * 2 + opp[-1]]


def mean_score(bits, opponents: list[Factory], rounds: int, noise: float, reps: int, seed: int) -> float:
    """Mittlere Auszahlung je Runde der Tabelle gegen jeden der Gegner (je `reps` Wiederholungen)."""
    rng = random.Random(seed)
    total = 0.0
    for make_opp in opponents:
        for _ in range(reps):
            total += play_match(TableStrategy(bits), make_opp(), rounds, noise, rng)[0]
    return total / (len(opponents) * reps)


def mean_score_of_strategy(key: str, opponents: list[Factory], rounds: int, noise: float, reps: int, seed: int) -> float:
    """Dieselbe Messung für eine Strategie des Feldes (z. B. Tit-for-Tat), mit demselben Seed-Verfahren wie `mean_score`."""
    rng = random.Random(seed)
    total = 0.0
    for make_opp in opponents:
        for _ in range(reps):
            total += play_match(make(key), make_opp(), rounds, noise, rng)[0]
    return total / (len(opponents) * reps)


def mutate(bits, rng: random.Random):
    """Ein oder zwei zufällige Bits kippen (Nachbarschaft des Hill-Climbings)."""
    new = list(bits)
    for _ in range(rng.choice((1, 1, 2))):
        j = rng.randrange(C.TABLE_BITS)
        new[j] ^= 1
    return tuple(new)


def train_table(opponents: list[Factory], seed: int, rounds: int = C.TRAIN_ROUNDS, noise: float = C.TRAIN_NOISE,
                reps: int = C.TRAIN_REPS, iters: int = C.TRAIN_ITERS):
    """Hill-Climbing: Start zufällig, Annahme bei nicht schlechterem Wert. Gibt (Bits, Trainingswert) zurück."""
    rng = random.Random(seed)
    bits = tuple(rng.randint(0, 1) for _ in range(C.TABLE_BITS))
    best = mean_score(bits, opponents, rounds, noise, reps, seed)
    for it in range(iters):
        cand = mutate(bits, rng)
        value = mean_score(cand, opponents, rounds, noise, reps, seed + it + 1)
        if value >= best:
            bits, best = cand, value
    return bits, best


def factories(keys) -> list[Factory]:
    return [(lambda k=k: make(k)) for k in keys]


def load_data() -> dict:
    """Vorgerechnete Tabelle und Aufteilungen (tools/precompute.py); die Tests rechnen Stichproben davon nach."""
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def trained_factory() -> Factory:
    bits = load_data()["table"]
    return lambda: TableStrategy(bits)
