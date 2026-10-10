"""Permalink (Begrenzen und Einrasten), Presets und Zufalls-Seed-Button."""

import random
from dataclasses import dataclass

import streamlit as st

import axt_constants as C

ALL_KEYS = C.STRATEGY_KEYS + (C.TRAINED_KEY,)


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: type
    default: object
    lo: float | None = None
    hi: float | None = None


SETTING_SPECS = {
    "field_select": SettingSpec("field", str, ",".join(C.STRATEGY_KEYS)),
    "noise_slider": SettingSpec("noise", float, C.DEFAULT_NOISE, C.NOISE_MIN, C.NOISE_MAX),
    "rounds_slider": SettingSpec("rounds", int, C.DEFAULT_ROUNDS, C.ROUNDS_MIN, C.ROUNDS_MAX),
    "seed_input": SettingSpec("seed", int, C.DEFAULT_SEED, 0, C.SEED_MAX),
}
PRESET_KEYS = {"field": "field_select", "noise": "noise_slider", "rounds": "rounds_slider"}


def parse_field(text: str) -> list[str]:
    """Aus der Adresszeile: gültige Strategienamen in der Reihenfolge von ALL_KEYS; unbekannte fallen weg, zu wenige -> alle 16."""
    wanted = {t.strip() for t in str(text).split(",") if t.strip()}
    keys = [k for k in ALL_KEYS if k in wanted]
    return keys if len(keys) >= 2 else list(C.STRATEGY_KEYS)


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = parse_field(spec.default) if state_key == "field_select" else spec.default


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def clamp(spec: SettingSpec, value):
    if spec.lo is not None:
        value = max(spec.lo, value)
    if spec.hi is not None:
        value = min(spec.hi, value)
    return value


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen, begrenzt bzw. auf gültige Strategien eingerastet."""
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param not in qp:
            continue
        raw = qp[spec.url_param]
        if isinstance(raw, list):
            raw = raw[0] if raw else ""
        if state_key == "field_select":
            st.session_state[state_key] = parse_field(raw)
            continue
        try:
            value = spec.caster(raw)
        except (ValueError, TypeError):
            continue
        st.session_state[state_key] = clamp(spec, value)
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = ",".join(value) if state_key == "field_select" else str(value)
    except Exception:
        pass


def apply_preset(name):
    for key, state_key in PRESET_KEYS.items():
        if key in C.PRESETS[name]:
            value = C.PRESETS[name][key]
            st.session_state[state_key] = list(value) if key == "field" else value


def randomize_seed():
    st.session_state["seed_input"] = random.randint(0, C.SEED_MAX)
