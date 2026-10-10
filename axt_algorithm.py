"""Kern der Demo (nur Standardbibliothek): das Rundenturnier und die Rangliste.

Jede Regel ist eine eigene Funktion mit expliziten Ein- und Ausgaben (DEMO-PLAYBOOK §1b):

- `flip`              Rauschen: die tatsächlich ausgeführte Aktion
- `play_match`        ein Spiel über `rounds` Runden: mittlere Auszahlung je Runde für beide
- `pair_seed`         Zufalls-Seed eines Paares, nur aus den Namen und dem Turnier-Seed (nicht aus der Position im Feld)
- `payoff_matrix`     alle Paare, Mittel über `reps` Wiederholungen: Zeile gegen Spalte
- `ranking`           Rangliste einer Teilmenge des Feldes aus der Matrix (ohne Selbstspiel)
- `subfield_outcomes` Rang einer Strategie und Sieger über zufällige Teilfelder

Weil jede Zelle der Matrix nur von ihren zwei Strategien abhängt, ist die Rangliste eines Teilfeldes immer ein Ausschnitt der Matrix:
„das Feld“ entscheidet nur, über welche Zeilen und Spalten gemittelt wird."""

import random
import zlib
from typing import Callable

import axt_constants as C
from axt_scenario import Strategy, stage_payoff

Factory = Callable[[], Strategy]


def flip(action: int, noise: float, rng: random.Random) -> int:
    """Die ausgeführte Aktion: mit Wahrscheinlichkeit `noise` die andere als die beabsichtigte."""
    if noise > 0.0 and rng.random() < noise:
        return 1 - action
    return action


def play_match(a: Strategy, b: Strategy, rounds: int, noise: float, rng: random.Random) -> tuple[float, float]:
    """Mittlere Auszahlung je Runde für a und b. Beide sehen die tatsächlich ausgeführten Aktionen."""
    a.reset()
    b.reset()
    ha: list[int] = []
    hb: list[int] = []
    total_a = total_b = 0.0
    for _ in range(rounds):
        x = flip(a.act(ha, hb, rng), noise, rng)
        y = flip(b.act(hb, ha, rng), noise, rng)
        ha.append(x)
        hb.append(y)
        total_a += stage_payoff(x, y)
        total_b += stage_payoff(y, x)
    return total_a / rounds, total_b / rounds


def pair_seed(seed: int, key_a: str, key_b: str) -> int:
    """Stabiler Seed je ungeordnetem Paar; unabhängig von der Reihenfolge der Strategien im Feld."""
    first, second = sorted((key_a, key_b))
    return seed * 1_000_003 + zlib.crc32(f"{first}|{second}".encode("utf-8"))


def payoff_matrix(field: list[tuple[str, Factory]], rounds: int, noise: float, reps: int, seed: int) -> list[list[float]]:
    """Mittlere Auszahlung je Runde, Zeile gegen Spalte; Diagonale = Spiel gegen eine Kopie seiner selbst."""
    n = len(field)
    mat = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i, n):
            key_i, make_i = field[i]
            key_j, make_j = field[j]
            rng = random.Random(pair_seed(seed, key_i, key_j))
            swap = key_i > key_j      # kanonische Spielreihenfolge: der Name vorn spielt als „a“, damit die Zufallsfolge nur vom Paar abhängt
            sum_i = sum_j = 0.0
            for _ in range(reps):
                if swap:
                    pj, pi = play_match(make_j(), make_i(), rounds, noise, rng)
                else:
                    pi, pj = play_match(make_i(), make_j(), rounds, noise, rng)
                sum_i += pi
                sum_j += pj
            mat[i][j] = sum_i / reps
            if i != j:
                mat[j][i] = sum_j / reps
    return mat


def ranking(matrix: list[list[float]], members: list[int]) -> tuple[list[int], dict[int, float]]:
    """Rangliste der Zeilen `members`: Mittel der Auszahlung gegen alle ANDEREN Mitglieder, absteigend; Gleichstand: kleinerer Index."""
    if len(members) < 2:
        raise ValueError("ein Turnier braucht mindestens zwei Strategien")
    score = {i: sum(matrix[i][j] for j in members if j != i) / (len(members) - 1) for i in members}
    order = sorted(members, key=lambda i: (-score[i], i))
    return order, score


TIE_TOL = 1e-9


def tied_rank(score: dict[int, float], member: int, tol: float = TIE_TOL) -> int:
    """Rang mit Gleichständen: 1 + Zahl der Mitglieder, die um mehr als `tol` besser sind (Gleichstand teilt den Rang)."""
    return 1 + sum(1 for s in score.values() if s > score[member] + tol)


def tied_winners(score: dict[int, float], tol: float = TIE_TOL) -> list[int]:
    """Alle Mitglieder, die um höchstens `tol` hinter dem Besten liegen."""
    best = max(score.values())
    return sorted(i for i, s in score.items() if s >= best - tol)


def subfield_outcomes(matrix: list[list[float]], keys: list[str], focus: str, size: int, draws: int, seed: int) -> dict:
    """Zufällige Teilfelder der Größe `size`, `focus` immer dabei: Rang von `focus` (mit Gleichständen) und Anteil je Sieger.

    Bei einem Gleichstand an der Spitze zählt jeder Sieger mit 1/Zahl der Gleichplatzierten."""
    if focus not in keys:
        raise ValueError(f"{focus} nicht im Feld")
    pos = keys.index(focus)
    others = [i for i in range(len(keys)) if i != pos]
    if size - 1 > len(others) or size < 2:
        raise ValueError("Teilfeldgröße passt nicht zum Feld")
    rng = random.Random(seed)
    ranks: list[int] = []
    winners: dict[str, float] = {}
    for _ in range(draws):
        members = rng.sample(others, size - 1) + [pos]
        _, score = ranking(matrix, members)
        ranks.append(tied_rank(score, pos))
        top = tied_winners(score)
        for i in top:
            winners[keys[i]] = winners.get(keys[i], 0.0) + 1.0 / len(top)
    return {"ranks": ranks, "winners": winners, "draws": draws}
