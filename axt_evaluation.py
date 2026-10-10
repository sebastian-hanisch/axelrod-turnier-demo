"""Kennzahlen, Verdikt-Logik und Auswertungen über den Kern (die Komposition der Einheiten aus axt_algorithm und axt_trained)."""

import statistics
from dataclasses import dataclass

import axt_algorithm as A
import axt_constants as C
import axt_trained as TR
from axt_scenario import CLASSES, make


def fmt(x: float, digits: int = 2) -> str:
    """Zahl mit deutschem Dezimalkomma."""
    return f"{x:.{digits}f}".replace(".", ",")


def label_of(key: str) -> str:
    return TR.TableStrategy.label if key == C.TRAINED_KEY else CLASSES[key].label


def field_entries(keys) -> list[tuple[str, A.Factory]]:
    out = []
    for key in keys:
        out.append((key, TR.trained_factory() if key == C.TRAINED_KEY else (lambda k=key: make(k))))
    return out


@dataclass(frozen=True)
class Settings:
    field: tuple[str, ...] = C.STRATEGY_KEYS
    noise: float = C.DEFAULT_NOISE
    rounds: int = C.DEFAULT_ROUNDS
    seed: int = C.DEFAULT_SEED


@dataclass(frozen=True)
class Analysis:
    keys: tuple[str, ...]
    matrix: tuple[tuple[float, ...], ...]
    order: tuple[int, ...]                       # Indizes, beste zuerst
    scores: tuple[float, ...]                    # mittlere Auszahlung je Runde gegen die anderen, je Index
    winners: tuple[str, ...]                     # alle Strategien an der Spitze (bei Gleichstand mehrere)
    tft_rank: int | None                         # Rang mit Gleichständen (ein Gleichstand teilt den Rang)
    tft_score: float | None
    tft_beats_nobody: bool | None                # ohne Rauschen: TFT erzielt gegen keinen Gegner mehr als der Gegner (None, wenn nicht prüfbar)


def analyse(settings: Settings) -> Analysis:
    keys = tuple(settings.field)
    if len(keys) < 2:
        raise ValueError("mindestens zwei Strategien")
    mat = A.payoff_matrix(field_entries(keys), settings.rounds, settings.noise, C.REPS, settings.seed)
    order, score = A.ranking(mat, list(range(len(keys))))
    tft_rank = tft_score = beats_nobody = None
    if "TFT" in keys:
        t = keys.index("TFT")
        tft_rank = A.tied_rank(score, t)
        tft_score = score[t]
        if settings.noise == 0.0:
            beats_nobody = all(mat[t][j] <= mat[j][t] + 1e-9 for j in range(len(keys)) if j != t)
    return Analysis(
        keys=keys,
        matrix=tuple(tuple(r) for r in mat),
        order=tuple(order),
        scores=tuple(score[i] for i in range(len(keys))),
        winners=tuple(keys[i] for i in A.tied_winners(score)),
        tft_rank=tft_rank,
        tft_score=tft_score,
        tft_beats_nobody=beats_nobody,
    )


def noise_ranks(settings: Settings, levels=C.NOISE_LEVELS) -> dict[float, dict[str, int]]:
    """Rang jeder Strategie des Feldes bei den Rauschstufen `levels`."""
    out = {}
    for level in levels:
        an = analyse(Settings(settings.field, level, settings.rounds, settings.seed))
        score = {i: an.scores[i] for i in range(len(an.keys))}
        out[level] = {an.keys[i]: A.tied_rank(score, i) for i in range(len(an.keys))}
    return out


def subfields(an: Analysis, size: int = C.SUBFIELD_SIZE, draws: int = C.SUBFIELD_DRAWS) -> dict | None:
    """Rang von Tit-for-Tat und Sieger über zufällige Teilfelder; None, wenn das Feld zu klein ist oder TFT fehlt."""
    if "TFT" not in an.keys or len(an.keys) < size:
        return None
    mat = [list(r) for r in an.matrix]
    res = A.subfield_outcomes(mat, list(an.keys), "TFT", size, draws, C.SUBFIELD_SEED)
    ranks = res["ranks"]
    res["median_rank"] = statistics.median(ranks)
    res["win_share"] = sum(1 for r in ranks if r == 1) / len(ranks)
    res["top_winners"] = sorted(res["winners"].items(), key=lambda kv: (-kv[1], kv[0]))
    return res


def action_string(actions) -> str:
    """Aktionsfolge als „C D D …“ (C = kooperiert, D = defektiert)."""
    return " ".join("C" if a == C.COOPERATE else "D" for a in actions)


def strategy_overview(rounds: int = 12, seed: int = 1) -> list[dict]:
    """Je Strategie: Beschreibung und die eigenen ersten `rounds` Aktionen gegen Immer-Defektieren und gegen einen Abwechsler (C, D, C, D, …).

    Bei Zufalls-Strategien ist die Spur ein Beispiel mit festem Seed. Die Spuren machen sichtbar, was die Worte meinen."""
    import random

    rows = []
    for key in C.STRATEGY_KEYS:
        cls = CLASSES[key]
        traces = {}
        for opp_key in ("ALLD", "ALTERNATOR"):
            a, b, rng = make(key), make(opp_key), random.Random(seed)
            a.reset()
            b.reset()
            own, opp = [], []
            for _ in range(rounds):
                x = a.act(own, opp, rng)
                y = b.act(opp, own, rng)
                own.append(x)
                opp.append(y)
            traces[opp_key] = action_string(own)
        rows.append({"key": key, "label": cls.label, "description": cls.description, "nice": cls.nice,
                     "vs_alld": traces["ALLD"], "vs_alt": traces["ALTERNATOR"]})
    return rows


def split_summary() -> dict:
    """Die 20 vorgerechneten Aufteilungen: wie oft schlägt die trainierte Tabelle TFT im Training und auf ungesehenen Gegnern."""
    splits = TR.load_data()["splits"]
    train_diff = [s["train_table"] - s["train_tft"] for s in splits]
    test_diff = [s["test_table"] - s["test_tft"] for s in splits]
    return {
        "n": len(splits),
        "train_diff": train_diff,
        "test_diff": test_diff,
        "train_wins": sum(1 for d in train_diff if d > 0),
        "test_wins": sum(1 for d in test_diff if d > 0),
        "mean_train_diff": statistics.mean(train_diff),
        "mean_test_diff": statistics.mean(test_diff),
        "worst_test_diff": min(test_diff),
    }


def verdict(an: Analysis, settings: Settings) -> tuple[str, str]:
    """(Stufe, Satz) für die Kernfrage: gewinnt Tit-for-Tat dieses Feld?"""
    if an.tft_rank is None:
        return "info", f"Tit-for-Tat ist nicht im Feld. Sieger: **{label_of(an.winner)}**."
    n = len(an.keys)
    extra = ""
    if an.tft_beats_nobody:
        extra = " Dabei erzielt es gegen **keinen** Gegner mehr Punkte als der Gegner: Tit-for-Tat gewinnt kein einziges Spiel."
    if an.tft_rank == 1:
        if len(an.winners) == 1:
            return "success", f"Tit-for-Tat gewinnt dieses Feld ({n} Strategien, {fmt(an.tft_score)} Punkte je Runde im Mittel).{extra}"
        others = ", ".join(label_of(k) for k in an.winners if k != "TFT")
        return "info", (f"Tit-for-Tat **teilt Rang 1** mit {others} ({fmt(an.tft_score)} Punkte je Runde): in diesem Feld gibt es "
                        f"nichts zu entscheiden.{extra}")
    best = an.scores[an.keys.index(an.winners[0])]
    names = " und ".join(label_of(k) for k in an.winners)
    return "warning", (f"Tit-for-Tat belegt Rang **{an.tft_rank} von {n}** ({fmt(an.tft_score)} Punkte je Runde); es gewinnt "
                       f"**{names}** ({fmt(best)}).{extra}")
