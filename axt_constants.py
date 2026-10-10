"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

COOPERATE, DEFECT = 0, 1

# Auszahlungen je Runde (Axelrod): fest, kein Regler (Stück 1 der Linie hat sie variiert).
T, R, P, S = 5.0, 3.0, 1.0, 0.0

ROUNDS_MIN, ROUNDS_MAX, DEFAULT_ROUNDS, ROUNDS_STEP = 50, 500, 200, 50
NOISE_MIN, NOISE_MAX, DEFAULT_NOISE, NOISE_STEP = 0.0, 0.10, 0.0, 0.01
REPS = 20                                    # Wiederholungen je Paar (stochastische Strategien, Rauschen)
SEED_MAX, DEFAULT_SEED = 999999, 20260

NOISE_LEVELS = (0.0, 0.01, 0.05)             # Stufen des Rausch-Experiments (wie im Preprint von Knight et al. 2025)
SUBFIELD_SIZE = 8                            # Teilfelder: 8 Strategien, TFT immer dabei
SUBFIELD_DRAWS = 2000
SUBFIELD_SEED = 7

STRATEGY_KEYS = (
    "ALLC", "ALLD", "TFT", "STFT", "GRIM", "TF2T", "HARD_TFT", "PAVLOV",
    "JOSS", "GTFT", "PROBER", "RANDOM", "ALTERNATOR", "DAVIS", "GRADUAL", "BULLY",
)
TRAINED_KEY = "TRAINIERT"
NICE_KEYS = ("ALLC", "TFT", "GRIM", "TF2T", "HARD_TFT", "PAVLOV", "GTFT", "DAVIS", "GRADUAL")
NASTY_KEYS = ("ALLD", "STFT", "BULLY", "PROBER", "JOSS", "RANDOM", "ALTERNATOR")

# Trainierte Tabelle: Kontext = die letzten zwei Runden beider Spieler (16 Kontexte) plus zwei Startzüge.
TABLE_BITS = 18
TRAIN_ROUNDS, TRAIN_NOISE, TRAIN_REPS, TRAIN_ITERS = 100, 0.01, 3, 400
SPLIT_TRAIN, SPLIT_COUNT = 10, 20            # je Aufteilung: 10 Trainings-, 6 Testgegner; 20 Aufteilungen

COLOR_NICE = "#2F6B65"
COLOR_NASTY = "#B5483A"
COLOR_TFT = "#4c78a8"
COLOR_TRAINED = "#e08a2c"
COLOR_OTHER = "rgba(150,150,150,0.55)"

PRESETS = {
    "Alle 16 Strategien (Voreinstellung)": {"field": STRATEGY_KEYS, "noise": 0.0, "rounds": DEFAULT_ROUNDS},
    "Nur nette Strategien": {"field": NICE_KEYS, "noise": 0.0, "rounds": DEFAULT_ROUNDS},
    "Nur nette, 1 % Rauschen": {"field": NICE_KEYS, "noise": 0.01, "rounds": DEFAULT_ROUNDS},
    "Böse Mehrheit": {"field": ("TFT",) + NASTY_KEYS + ("ALLC", "GRIM"), "noise": 0.0, "rounds": DEFAULT_ROUNDS},
    "Alle 16, 1 % Rauschen": {"field": STRATEGY_KEYS, "noise": 0.01, "rounds": DEFAULT_ROUNDS},
    "Alle 16, 5 % Rauschen": {"field": STRATEGY_KEYS, "noise": 0.05, "rounds": DEFAULT_ROUNDS},
}
PRESET_HELP = {
    "Alle 16 Strategien (Voreinstellung)": "Das ganze Feld ohne Fehler: wer liegt vorn, und wo steht Tit-for-Tat?",
    "Nur nette Strategien": "Neun Strategien, die nie als Erste defektieren: ohne Fehler erzielen alle genau 3,00, es gibt nichts zu entscheiden.",
    "Nur nette, 1 % Rauschen": "Dieselben neun mit Fehlgriffen: jetzt entscheidet der Umgang mit Fehlern. Tit-for-Tat belegt Rang 4 von 9.",
    "Böse Mehrheit": "Sieben bösartige Strategien plus Tit-for-Tat, Immer-Kooperieren und Grim Trigger: Grim Trigger gewinnt, Tit-for-Tat belegt Rang 4 von 10.",
    "Alle 16, 1 % Rauschen": "Jede Aktion wird mit 1 % Wahrscheinlichkeit verwechselt (Fehlgriff).",
    "Alle 16, 5 % Rauschen": "Jede Aktion wird mit 5 % Wahrscheinlichkeit verwechselt.",
}
