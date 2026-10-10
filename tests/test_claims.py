"""Jede Zahl aus README und App wird hier über die echten Auswertungsfunktionen nachgerechnet (DEMO-PLAYBOOK §4)."""

import pytest

import axt_constants as C
import axt_evaluation as E
import axt_trained as TR

DEFAULT = E.Settings()                      # 16 klassische Strategien, 200 Runden, kein Rauschen, Seed 20260


@pytest.fixture(scope="module")
def default_analysis():
    return E.analyse(DEFAULT)


def test_default_field_ranking_and_tft_position(default_analysis):
    an = default_analysis
    top = [(an.keys[i], an.scores[i]) for i in an.order[:5]]
    assert [k for k, _ in top] == ["GRADUAL", "GRIM", "DAVIS", "GTFT", "TF2T"]
    assert top[0][1] == pytest.approx(2.756, abs=0.01)
    assert an.winners == ("GRADUAL",)
    assert an.tft_rank == 6 and an.tft_score == pytest.approx(2.461, abs=0.01)


def test_tft_wins_no_single_match_without_noise(default_analysis):
    assert default_analysis.tft_beats_nobody is True


def test_nothing_to_decide_among_the_nice_strategies_without_noise():
    an = E.analyse(E.Settings(field=C.NICE_KEYS))
    assert len(an.winners) == 9 and an.tft_rank == 1
    assert all(s == pytest.approx(3.0) for s in an.scores)
    assert E.verdict(an, E.Settings(field=C.NICE_KEYS))[0] == "info"


def test_nice_strategies_with_one_percent_noise_tft_is_fourth_of_nine():
    s = E.Settings(field=C.NICE_KEYS, noise=0.01)
    an = E.analyse(s)
    assert an.tft_rank == 4 and an.winners == ("GTFT",)


def test_nasty_majority_grim_wins_and_tft_is_fourth_of_ten():
    field = ("TFT",) + C.NASTY_KEYS + ("ALLC", "GRIM")
    an = E.analyse(E.Settings(field=field))
    assert an.winners == ("GRIM",) and an.tft_rank == 4 and len(an.keys) == 10
    assert an.tft_score == pytest.approx(2.102, abs=0.01)


def test_subfield_statistics_at_zero_noise(default_analysis):
    sub = E.subfields(default_analysis)
    assert sub["median_rank"] == 3.0
    assert sub["win_share"] == pytest.approx(0.049, abs=0.012)
    assert [k for k, _ in sub["top_winners"][:2]] == ["GRADUAL", "GRIM"]
    assert sub["winners"]["GRADUAL"] / sub["draws"] == pytest.approx(0.29, abs=0.03)


def test_tft_rank_over_the_noise_levels():
    ranks = E.noise_ranks(DEFAULT)
    assert [ranks[l]["TFT"] for l in C.NOISE_LEVELS] == [6, 6, 7]
    assert all(min(r, key=r.get) == "GRADUAL" for r in ranks.values())


def test_trained_table_wins_its_own_training_field():
    an = E.analyse(E.Settings(field=C.STRATEGY_KEYS + (C.TRAINED_KEY,)))
    assert an.winners == (C.TRAINED_KEY,) and an.tft_rank == 7


def test_split_summary_numbers():
    sp = E.split_summary()
    assert sp["n"] == 20 and sp["train_wins"] == 19 and sp["test_wins"] == 14
    assert sp["mean_train_diff"] == pytest.approx(0.434, abs=0.005)
    assert sp["mean_test_diff"] == pytest.approx(0.165, abs=0.005)
    assert sp["worst_test_diff"] == pytest.approx(-0.449, abs=0.005)


def test_precomputed_splits_are_reproducible():
    """Stichprobe der vorgerechneten Daten (tools/precompute.py): zwei Aufteilungen und die ausgelieferte Tabelle werden neu gerechnet."""
    import importlib.util
    import pathlib

    spec = importlib.util.spec_from_file_location("precompute", pathlib.Path(__file__).resolve().parent.parent / "tools" / "precompute.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    data = TR.load_data()
    for index in (0, 7):
        fresh = mod.compute_split(index)
        stored = data["splits"][index]
        assert fresh["bits"] == stored["bits"], index
        assert fresh["train"] == stored["train"] and fresh["test"] == stored["test"]
        for field in ("train_table", "train_tft", "test_table", "test_tft"):
            assert fresh[field] == pytest.approx(stored[field], abs=1e-9), (index, field)
    bits, _ = TR.train_table(TR.factories(C.STRATEGY_KEYS), seed=data["table_seed"])
    assert list(bits) == data["table"]


def test_strategy_overview_traces_by_hand():
    rows = {r["key"]: r for r in E.strategy_overview()}
    assert rows["TFT"]["vs_alld"] == "C D D D D D D D D D D D"
    assert rows["GRIM"]["vs_alt"] == "C C D D D D D D D D D D"
    assert rows["TF2T"]["vs_alt"] == "C C C C C C C C C C C C"          # nie zweimal in Folge defektiert: wird dauerhaft ausgebeutet
    assert rows["DAVIS"]["vs_alld"] == "C C C C C C C C C C D D"
    assert rows["GRADUAL"]["vs_alld"].startswith("C D C C D D C C D D D C")
    assert rows["ALLC"]["nice"] and not rows["ALLD"]["nice"]
    assert len(rows) == 16 and all(r["description"] for r in rows.values())


def test_verdict_texts(default_analysis):
    level, text = E.verdict(default_analysis, DEFAULT)
    assert level == "warning" and "Rang **6 von 16**" in text and "Gradual" in text and "keinen" in text
