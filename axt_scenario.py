"""Szenario: das Gefangenendilemma mit den Auszahlungen 5/3/1/0 und die 16 Strategien des Feldes.

Jede Strategie ist eine kleine Klasse mit `act(own_history, opp_history, rng)`: die Aktion der nächsten Runde aus den bisherigen
Aktionen BEIDER Spieler (bei Rauschen die tatsächlich ausgeführten). Zufall nur über das übergebene `rng`."""

import random

import axt_constants as C


def stage_payoff(own: int, other: int) -> float:
    """Auszahlung einer Runde für die eigene Aktion gegen die des anderen (0 = C, 1 = D)."""
    if own == C.COOPERATE:
        return C.R if other == C.COOPERATE else C.S
    return C.T if other == C.COOPERATE else C.P


class Strategy:
    key = "?"
    label = "?"
    description = ""
    nice = True                      # defektiert nie als Erste (ohne Rauschen)

    def reset(self) -> None:
        """Interner Zustand zurück auf Anfang (nur Strategien mit eigenem Zustand überschreiben das)."""

    def act(self, own: list[int], opp: list[int], rng: random.Random) -> int:
        raise NotImplementedError


class AllC(Strategy):
    key, label = "ALLC", "Immer kooperieren"
    description = "Kooperiert in jeder Runde."

    def act(self, own, opp, rng):
        return C.COOPERATE


class AllD(Strategy):
    key, label, nice = "ALLD", "Immer defektieren", False
    description = "Defektiert in jeder Runde."

    def act(self, own, opp, rng):
        return C.DEFECT


class TFT(Strategy):
    key, label = "TFT", "Tit-for-Tat"
    description = "Kooperiert zuerst, danach die letzte Aktion des Gegners."

    def act(self, own, opp, rng):
        return opp[-1] if opp else C.COOPERATE


class STFT(Strategy):
    key, label, nice = "STFT", "Misstrauisches Tit-for-Tat", False
    description = "Defektiert zuerst, danach die letzte Aktion des Gegners."

    def act(self, own, opp, rng):
        return opp[-1] if opp else C.DEFECT


class Grim(Strategy):
    key, label = "GRIM", "Grim Trigger"
    description = "Kooperiert, bis der Gegner einmal defektiert hat; danach immer defektieren."

    def act(self, own, opp, rng):
        return C.DEFECT if C.DEFECT in opp else C.COOPERATE


class TF2T(Strategy):
    key, label = "TF2T", "Tit-for-Two-Tats"
    description = "Defektiert erst, wenn der Gegner zweimal in Folge defektiert hat."

    def act(self, own, opp, rng):
        return C.DEFECT if len(opp) >= 2 and opp[-1] == C.DEFECT and opp[-2] == C.DEFECT else C.COOPERATE


class HardTFT(Strategy):
    key, label = "HARD_TFT", "Hartes Tit-for-Tat"
    description = "Defektiert, wenn der Gegner in einer der letzten beiden Runden defektiert hat."

    def act(self, own, opp, rng):
        return C.DEFECT if C.DEFECT in opp[-2:] else C.COOPERATE


class Pavlov(Strategy):
    key, label = "PAVLOV", "Pavlov"
    description = "Behält die eigene letzte Aktion, wenn der Gegner kooperiert hat, und wechselt sie sonst."

    def act(self, own, opp, rng):
        if not own:
            return C.COOPERATE
        return own[-1] if opp[-1] == C.COOPERATE else 1 - own[-1]


class Joss(Strategy):
    key, label, nice = "JOSS", "Joss", False
    description = "Tit-for-Tat, aber nach einer Kooperation des Gegners defektiert es mit 10 % Wahrscheinlichkeit trotzdem."

    def act(self, own, opp, rng):
        if not opp:
            return C.COOPERATE
        if opp[-1] == C.COOPERATE and rng.random() < 0.1:
            return C.DEFECT
        return opp[-1]


class GTFT(Strategy):
    key, label = "GTFT", "Großzügiges Tit-for-Tat"
    description = "Tit-for-Tat, vergibt aber eine Defektion des Gegners mit Wahrscheinlichkeit 1/3."

    def act(self, own, opp, rng):
        if not opp or opp[-1] == C.COOPERATE:
            return C.COOPERATE
        return C.COOPERATE if rng.random() < 1 / 3 else C.DEFECT


class Prober(Strategy):
    key, label, nice = "PROBER", "Naiver Prober", False
    description = "Tit-for-Tat mit gelegentlichem Testen: nach einer Kooperation defektiert es mit 10 % Wahrscheinlichkeit, um den Gegner zu prüfen."

    def act(self, own, opp, rng):
        if not opp:
            return C.COOPERATE
        if opp[-1] == C.COOPERATE and rng.random() < 0.1:
            return C.DEFECT
        return opp[-1]


class RandomStrategy(Strategy):
    key, label, nice = "RANDOM", "Zufall", False
    description = "Wirft jede Runde eine faire Münze."

    def act(self, own, opp, rng):
        return C.DEFECT if rng.random() < 0.5 else C.COOPERATE


class Alternator(Strategy):
    key, label, nice = "ALTERNATOR", "Abwechsler", False
    description = "Kooperiert und defektiert im Wechsel, beginnend mit Kooperation."

    def act(self, own, opp, rng):
        return len(own) % 2


class Davis(Strategy):
    key, label = "DAVIS", "Davis"
    description = "Kooperiert die ersten zehn Runden bedingungslos, danach wie Grim Trigger."

    def act(self, own, opp, rng):
        if len(own) < 10:
            return C.COOPERATE
        return C.DEFECT if C.DEFECT in opp else C.COOPERATE


class Gradual(Strategy):
    key, label = "GRADUAL", "Gradual"
    description = ("Kooperiert, bis der Gegner defektiert. Bei der n-ten Defektion defektiert es n-mal und kooperiert danach zweimal "
                   "zur Beruhigung (Beaufils, Delahaye und Mathieu 1997).")

    def __init__(self):
        self.reset()

    def reset(self):
        self.count = 0      # bisher bestrafte Defektionen des Gegners
        self.punish = 0     # noch ausstehende Strafrunden
        self.calm = 0       # noch ausstehende Beruhigungsrunden

    def act(self, own, opp, rng):
        if self.punish == 0 and self.calm == 0 and opp and opp[-1] == C.DEFECT:
            self.count += 1
            self.punish = self.count
            self.calm = 2
        if self.punish > 0:
            self.punish -= 1
            return C.DEFECT
        if self.calm > 0:
            self.calm -= 1
            return C.COOPERATE
        return C.COOPERATE


class Bully(Strategy):
    key, label, nice = "BULLY", "Rüpel", False
    description = "Tut das Gegenteil der letzten Aktion des Gegners, beginnend mit Defektion."

    def act(self, own, opp, rng):
        if not opp:
            return C.DEFECT
        return C.DEFECT if opp[-1] == C.COOPERATE else C.COOPERATE


_CLASSES = (AllC, AllD, TFT, STFT, Grim, TF2T, HardTFT, Pavlov, Joss, GTFT, Prober, RandomStrategy, Alternator, Davis, Gradual, Bully)
CLASSES = {cls.key: cls for cls in _CLASSES}
assert tuple(CLASSES) == C.STRATEGY_KEYS


def make(key: str) -> Strategy:
    """Frische Instanz (Zustand zurückgesetzt) der Strategie `key`."""
    return CLASSES[key]()
