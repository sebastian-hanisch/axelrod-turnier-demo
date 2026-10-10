"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, Permalink-Begrenzen/Einrasten."""

import axt_constants as C
import axt_evaluation as ev
import axt_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds():
    for name, preset in C.PRESETS.items():
        assert C.NOISE_MIN <= preset["noise"] <= C.NOISE_MAX, name
        assert C.ROUNDS_MIN <= preset["rounds"] <= C.ROUNDS_MAX, name
        assert len(preset["field"]) >= 2 and set(preset["field"]) <= set(P.ALL_KEYS), name
        assert round(preset["noise"] / C.NOISE_STEP) * C.NOISE_STEP == preset["noise"] or abs(preset["noise"] % C.NOISE_STEP) < 1e-9, name


def test_default_preset_equals_the_default_settings():
    first = next(iter(C.PRESETS.values()))
    s = ev.Settings(field=tuple(first["field"]), noise=first["noise"], rounds=first["rounds"])
    assert s == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) <= set(P.SETTING_SPECS)


def test_parse_field_keeps_valid_names_in_order_and_falls_back():
    assert P.parse_field("GRIM,TFT") == ["TFT", "GRIM"]
    assert P.parse_field("TFT,gibt-es-nicht,ALLD") == ["ALLD", "TFT"]
    assert P.parse_field("TFT") == list(C.STRATEGY_KEYS)
    assert P.parse_field("") == list(C.STRATEGY_KEYS)


def test_clamp_limits_numbers():
    spec = P.SETTING_SPECS["noise_slider"]
    assert P.clamp(spec, 0.7) == C.NOISE_MAX and P.clamp(spec, -1.0) == C.NOISE_MIN


def test_nice_and_nasty_sets_partition_the_classic_field_without_the_nice_label_lying():
    from axt_scenario import CLASSES
    assert set(C.NICE_KEYS) | set(C.NASTY_KEYS) == set(C.STRATEGY_KEYS)
    assert set(C.NICE_KEYS) & set(C.NASTY_KEYS) == set()
    for k in C.NICE_KEYS:
        assert CLASSES[k].nice, k
    for k in C.NASTY_KEYS:
        assert not CLASSES[k].nice, k
