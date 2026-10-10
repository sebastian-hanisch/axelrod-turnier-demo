"""Rechnet die trainierte Tabelle und die 20 Trainings-/Test-Aufteilungen vor und schreibt axt_data.json.

Aufruf (aus dem Demo-Ordner): python tools/precompute.py
Alles ist deterministisch (feste Seeds); tests/test_claims.py rechnet Stichproben davon nach."""

import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import axt_constants as C  # noqa: E402
import axt_trained as TR  # noqa: E402

EVAL_ROUNDS, EVAL_NOISE, EVAL_REPS, EVAL_SEED = 200, 0.01, 10, 99
TABLE_SEED = 20261


def evaluate(bits, keys):
    opp = TR.factories(keys)
    table = TR.mean_score(bits, opp, EVAL_ROUNDS, EVAL_NOISE, EVAL_REPS, EVAL_SEED)
    tft = TR.mean_score_of_strategy("TFT", opp, EVAL_ROUNDS, EVAL_NOISE, EVAL_REPS, EVAL_SEED)
    return table, tft


def split_keys(index):
    rng = random.Random(1000 + index)
    keys = list(C.STRATEGY_KEYS)
    rng.shuffle(keys)
    return keys[: C.SPLIT_TRAIN], keys[C.SPLIT_TRAIN:]


def compute_split(index):
    train_keys, test_keys = split_keys(index)
    bits, _ = TR.train_table(TR.factories(train_keys), seed=5000 + index)
    tr_table, tr_tft = evaluate(bits, train_keys)
    te_table, te_tft = evaluate(bits, test_keys)
    return {"index": index, "train": train_keys, "test": test_keys, "bits": list(bits),
            "train_table": tr_table, "train_tft": tr_tft, "test_table": te_table, "test_tft": te_tft}


def main():
    t0 = time.time()
    bits, _ = TR.train_table(TR.factories(C.STRATEGY_KEYS), seed=TABLE_SEED)
    data = {"table": list(bits), "table_seed": TABLE_SEED, "splits": []}
    for i in range(C.SPLIT_COUNT):
        data["splits"].append(compute_split(i))
        print(f"Aufteilung {i}: Training {data['splits'][-1]['train_table']:.3f} gegen TFT {data['splits'][-1]['train_tft']:.3f}, "
              f"Test {data['splits'][-1]['test_table']:.3f} gegen TFT {data['splits'][-1]['test_tft']:.3f}  ({time.time() - t0:.0f} s)", flush=True)
    (ROOT / "axt_data.json").write_text(json.dumps(data, indent=1), encoding="utf-8")
    print("geschrieben:", ROOT / "axt_data.json")


if __name__ == "__main__":
    main()
