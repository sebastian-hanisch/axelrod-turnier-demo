"""Axelrod-Turnier: wer gewinnt, hängt am Feld - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Zweites Stück der Wiederholte-Spiele-Linie: 16 klassische Strategien spielen im wiederholten Gefangenendilemma jeder gegen jeden. Gezeigt wird,
dass die Rangliste vom Feld abhängt (Teilfelder), vom Rauschen und davon, ob eine trainierte Strategie auf ungesehene Gegner trifft.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import axt_constants as C
import axt_evaluation as E
from axt_evaluation import Settings, fmt, label_of
from axt_presets import (
    ALL_KEYS,
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sync_query_params,
)
from axt_scenario import CLASSES
from axt_visualization import build_matrix, build_noise_ranks, build_rank_hist, build_ranking, build_split_bars, build_winner_bars

st.set_page_config(page_title="Axelrod-Turnier: wer gewinnt, hängt am Feld – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return E.analyse(settings)


@st.cache_data(show_spinner=False)
def _subfields(settings):
    return E.subfields(E.analyse(settings))


@st.cache_data(show_spinner=False)
def _noise_ranks(settings):
    return E.noise_ranks(settings)


@st.cache_data(show_spinner=False)
def _splits():
    return E.split_summary()


st.title("🏆 Axelrod-Turnier: wer gewinnt, hängt am Feld")
st.markdown(
    """
1980 ließ Robert Axelrod Computerprogramme im wiederholten Gefangenendilemma **jeder gegen jeden** antreten. Gewonnen hat **Tit-for-Tat**,
das einfachste Programm im Feld. Diese Demo lässt 16 klassische Strategien über 200 Runden gegeneinander spielen und stellt die Frage, die
man dem Ergebnis selten stellt: **Wie viel davon hängt am Teilnehmerfeld?** Dasselbe Turnier mit anderen Teilnehmern, mit Fehlgriffen
oder mit einer trainierten Strategie gibt andere Sieger.

Weiter unten: der Abschnitt **❓ Kernfrage**, drei Experimente (**🔬**), **🚧 Wo die Annahmen enden** und der Expander
**📐 Mathematische Formulierung**. Vorgänger ist [tit-for-tat-demo](https://sebastianhanisch-tit-for-tat-demo.streamlit.app/): dort ging
es um die Frage, ab wann Vergeltung Kooperation stabil hält, hier um das Abschneiden im Feld.
"""
)

with st.expander("So funktioniert ein Rundenturnier", expanded=True):
    st.markdown(
        """
1. **Jedes Paar spielt** 20 Wiederholungen über die eingestellte Rundenzahl; die Auszahlungen sind 5/3/1/0 (nur nutzen / beide tauschen /
   keiner tauscht / angeboten, nichts bekommen).
2. **Die Wertung** ist die mittlere Auszahlung je Runde gegen **alle anderen** Teilnehmer des Feldes (ohne Spiel gegen sich selbst).
3. **Das Feld entscheidet:** Jede Zelle der Auszahlungsmatrix hängt nur von ihren zwei Strategien ab. Ein anderes Feld heißt nur, dass über
   andere Zeilen und Spalten gemittelt wird, und das kann die Rangfolge umdrehen.
        """
    )

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
cols = st.columns(len(C.PRESETS))
for col, name in zip(cols, C.PRESETS):
    with col:
        st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    st.markdown("**Feld**")
    field = st.multiselect("Teilnehmer", ALL_KEYS, key="field_select", format_func=label_of,
                           help="Wer mitspielt. „Trainierte Tabelle“ ist auf die 16 klassischen Strategien trainiert und tritt hier gegen ihre eigenen Trainingsgegner an.")
    st.markdown("**Spiel**")
    noise = st.slider("Rauschen (Verwechslung je Aktion)", *bounds("noise_slider"), step=C.NOISE_STEP, key="noise_slider",
                      help="Wahrscheinlichkeit, dass die ausgeführte Aktion die andere ist als die beabsichtigte. Beide Spieler sehen die ausgeführte Aktion.")
    rounds = st.slider("Runden je Spiel", *bounds("rounds_slider"), step=C.ROUNDS_STEP, key="rounds_slider",
                       help="Länge eines Spiels. Axelrod verwendete 200.")
    st.caption(f"Je Paar {C.REPS} Wiederholungen (wegen der Zufalls-Strategien und des Rauschens).")
    seed = st.number_input("Zufalls-Seed des Turniers", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neues Turnier würfeln", width="stretch", on_click=randomize_seed)

field = tuple(k for k in ALL_KEYS if k in field)
sync_query_params({"field_select": list(field), "noise_slider": round(float(noise), 2), "rounds_slider": int(rounds), "seed_input": int(seed)})

if len(field) < 2:
    st.warning("Ein Turnier braucht mindestens zwei Teilnehmer. Bitte in der Seitenleiste mindestens zwei Strategien wählen.")
    st.stop()

settings = Settings(field, round(float(noise), 2), int(rounds), int(seed))
with st.spinner("Das Turnier läuft ..."):
    an = _analysis(settings)
labels = {k: label_of(k) for k in an.keys}

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Rangliste")
m1, m2, m3, m4 = st.columns(4)
winner_text = " und ".join(labels[k] for k in an.winners) if len(an.winners) <= 2 else f"{len(an.winners)} gleichauf"
m1.metric("Sieger", winner_text, delta=f"{fmt(max(an.scores))} Punkte je Runde", delta_color="off")
if an.tft_rank is not None:
    m2.metric("Rang von Tit-for-Tat", f"{an.tft_rank} von {len(an.keys)}", delta=f"{fmt(an.tft_score)} Punkte je Runde", delta_color="off")
else:
    m2.metric("Rang von Tit-for-Tat", "nicht im Feld")
m3.metric("Teilnehmer", f"{len(an.keys)}", delta=f"{len(an.keys) * (len(an.keys) + 1) // 2} Paarungen", delta_color="off")
m4.metric("Spiele je Paarung", f"{settings.rounds} Runden", delta=f"{C.REPS} Wiederholungen · Rauschen {fmt(settings.noise * 100, 0)} %", delta_color="off")
st.plotly_chart(build_ranking(an.keys, an.order, an.scores, labels), width="stretch", key="ranking_chart")
st.caption("Blau: Tit-for-Tat · Orange: trainierte Tabelle · grün: nett (defektiert nie als Erste) · rot: bösartig.")

with st.expander("Auszahlungsmatrix: mittlere Auszahlung je Runde, Zeile gegen Spalte"):
    st.plotly_chart(build_matrix(an.keys, an.order, an.matrix, labels), width="stretch", key="matrix_chart")
    st.caption("Das Feld bestimmt nur, welche Zeilen und Spalten in den Mittelwert eingehen; die Zellen selbst hängen nur an ihren zwei Strategien.")

with st.expander("Die 16 Strategien: wer macht was?", expanded=True):
    st.markdown(
        "Jede Strategie entscheidet jede Runde, ob sie **kooperiert (C)** oder **defektiert (D)**, und kennt dafür die bisherigen Aktionen beider "
        "Spieler. **Nett** heißt: sie defektiert nie als Erste. Die beiden rechten Spalten zeigen, was die Strategie in den ersten zwölf Runden "
        "**selbst tut**, wenn der Gegner immer defektiert beziehungsweise abwechselnd kooperiert und defektiert (C, D, C, D, …). Bei den "
        "Zufalls-Strategien ist die Spur ein Beispiel."
    )
    rows = ["| Strategie | Verhalten | nett? | Gegen Immer-D | Gegen Abwechsler |", "|---|---|---|---|---|"]
    for r in E.strategy_overview():
        rows.append(f"| **{r['label']}** | {r['description']} | {'ja' if r['nice'] else 'nein'} | `{r['vs_alld']}` | `{r['vs_alt']}` |")
    st.markdown("\n".join(rows))

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Gewinnt Tit-for-Tat dieses Feld?")
level, sentence = E.verdict(an, settings)
{"success": st.success, "warning": st.warning, "info": st.info}[level](sentence)
st.markdown("---")

# --- Experiment 1: Teilfelder --------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Wie stabil ist die Rangliste, wenn das Feld anders zusammengesetzt ist?")
st.caption(
    f"{C.SUBFIELD_DRAWS} zufällige Teilfelder aus acht der gewählten Strategien, Tit-for-Tat immer dabei; die Ränge kommen aus derselben "
    "Auszahlungsmatrix, nur die Auswahl der Gegner ändert sich."
)
sub = _subfields(settings)
if sub is None:
    st.info(f"Dafür braucht das Feld Tit-for-Tat und mindestens {C.SUBFIELD_SIZE} Strategien.")
else:
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(build_rank_hist(sub["ranks"], C.SUBFIELD_SIZE), width="stretch", key="rank_hist")
    with c2:
        st.plotly_chart(build_winner_bars(sub["winners"], sub["draws"], labels), width="stretch", key="winner_bars")
    first_share = sub["win_share"] * 100
    st.info(
        f"In {fmt(first_share, 1)} % der Teilfelder gewinnt Tit-for-Tat, im Median belegt es Rang {fmt(sub['median_rank'], 1)} von {C.SUBFIELD_SIZE}. "
        f"Am häufigsten gewinnt {labels[sub['top_winners'][0][0]]} ({fmt(sub['top_winners'][0][1] / sub['draws'] * 100, 0)} % der Teilfelder). "
        "Welche Strategie „die beste“ ist, hängt also an den Gegnern."
    )
st.markdown("---")

# --- Experiment 2: Rauschen ----------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Wer steigt und wer fällt, wenn Fehler passieren?")
st.caption("Dasselbe Feld, dieselben Runden, Rauschen 0, 1 und 5 %: der Rang jeder Strategie. Hervorgehoben: Tit-for-Tat und der Sieger bei 0 %.")
with st.spinner("Drei Turniere mit unterschiedlichem Rauschen ..."):
    ranks_by_noise = _noise_ranks(settings)
st.plotly_chart(build_noise_ranks(ranks_by_noise, labels), width="stretch", key="noise_chart")
lv = list(ranks_by_noise)
if "TFT" in an.keys:
    tft_line = " → ".join(f"{ranks_by_noise[l]['TFT']}" for l in lv)
    st.info(f"Rang von Tit-for-Tat bei 0 / 1 / 5 % Rauschen: **{tft_line}** (von {len(an.keys)}). "
            "Fehler lösen bei Tit-for-Tat Echos aus, die ein nachsichtigeres Programm vermeidet.")
else:
    st.info("Tit-for-Tat ist nicht im Feld; die Linien zeigen die Ränge der gewählten Strategien.")
st.markdown("---")

# --- Experiment 3: trainierte Tabelle ------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Hilft Training gegen ein Feld auch gegen ungesehene Gegner?")
sp = _splits()
st.caption(
    f"Je Aufteilung ({sp['n']} Stück, vorgerechnet): eine Tabelle über die letzten zwei Runden beider Spieler wird per Hill-Climbing gegen "
    f"{C.SPLIT_TRAIN} der 16 Strategien trainiert und gegen die übrigen {len(C.STRATEGY_KEYS) - C.SPLIT_TRAIN} getestet, mit 1 % Rauschen."
)
st.plotly_chart(build_split_bars(sp["train_diff"], sp["test_diff"]), width="stretch", key="split_chart")
st.warning(
    f"Gegen die Trainingsgegner schlägt die Tabelle Tit-for-Tat in {sp['train_wins']} von {sp['n']} Aufteilungen (im Mittel "
    f"{fmt(sp['mean_train_diff'])} Punkte je Runde mehr). Gegen **ungesehene** Gegner nur noch in {sp['test_wins']} von {sp['n']} "
    f"(im Mittel {fmt(sp['mean_test_diff'])} mehr, im schlechtesten Fall {fmt(sp['worst_test_diff'])}). Der Vorsprung ist zum Teil "
    "Anpassung an die Trainingsgegner."
)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Das Feld besteht aus diesen 16 Strategien** | Es ist ein selbst zusammengestelltes Feld, nicht Axelrods Teilnehmerliste. Die Aussage „Tit-for-Tat gewinnt hier nicht“ gilt für dieses Feld; Axelrods Originalfeld reproduziert die Demo nicht. | - |
| **Wertung = Mittel gegen alle anderen** | Eine andere Wertung (Selbstspiel mitgezählt, Rangpunkte, Eliminationsrunden, evolutionäre Anteile) kann die Reihenfolge ändern. | - |
| **20 Wiederholungen je Paar** | Bei Zufalls-Strategien und Rauschen streuen die Zellen; der Seed ist fest, ein anderer Seed verschiebt Plätze mit kleinem Abstand. | - |
| **Trainiert wird gegen 10 von 16 Strategien mit 1 % Rauschen** | Kleines Feld, kurzes Training, eine Tabelle über zwei Runden Gedächtnis: das ist kein Nachbau der in der Literatur trainierten Strategien, die gegen mehr als 170 Gegner entstanden. | - |
| **Strategien sind fest** | Keine Anpassung während des Turniers, keine Population, die sich nach Erfolg vermehrt. | - |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Spiel.** Je Runde wählen beide Spieler $C$ oder $D$; Auszahlungen $(D,C)=5$, $(C,C)=3$, $(D,D)=1$, $(C,D)=0$. Eine Strategie
bildet die bisherigen Aktionen beider Spieler auf die nächste Aktion ab (gegebenenfalls zufällig). Bei Rauschen $\varepsilon$ wird die
beabsichtigte Aktion mit Wahrscheinlichkeit $\varepsilon$ ersetzt; beide Spieler sehen die ausgeführte Aktion.

**Auszahlungsmatrix.** $M_{ij}$ ist die mittlere Auszahlung je Runde von $i$ gegen $j$, gemittelt über $20$ Wiederholungen. Zufall kommt
nur aus einem Generator je Paar, dessen Seed aus dem Turnier-Seed und den Namen des Paares folgt: die Zelle hängt nicht von der Position
im Feld ab.

**Wertung.** Für ein Feld $F$ ist $s_i = \frac{1}{|F|-1}\sum_{j \in F,\, j \neq i} M_{ij}$. Der Rang ist $1 + |\{k : s_k > s_i\}|$, ein
Gleichstand teilt den Rang.

**Warum Tit-for-Tat ohne Rauschen nie ein Spiel gewinnt.** Mit $b_t$ als Aktion des Gegners und $b_0 = C$ spielt Tit-for-Tat in Runde
$t$ genau $b_{t-1}$. Die Punktdifferenz (Gegner minus Tit-for-Tat) ist die Summe der Terme $f(b_t, b_{t-1})$ mit
$f(x,y) = u(x,y) - u(y,x)$: sie ist nur bei einem Wechsel der Gegneraktion von null verschieden, $+5$ bei $C \to D$ und $-5$ bei $D \to C$.
Die Wechsel alternieren und beginnen bei $C$, also liegt die Summe nach jeder Runde in $\{0, 5\}$: Tit-for-Tat liegt nie vorn und höchstens
um einen Punktstand von 5 hinten. Siegen kann es im Turnier nur über die Summe vieler Spiele, in denen es gleichauf liegt.

**Trainierte Tabelle.** 16 Kontexte (die letzten zwei Aktionen beider Spieler) plus zwei Startzüge, 18 Bits. Hill-Climbing: ein oder zwei
zufällige Bits kippen, behalten, wenn die mittlere Auszahlung gegen die Trainingsgegner nicht sinkt (400 Schritte).

**Literatur.** Axelrod (1980), *Effective choice in the prisoner's dilemma*, Journal of Conflict Resolution 24 (erstes Turnier: 14
Einsendungen plus Zufall, 200 Züge; Tit-for-Tat von Anatol Rapoport gewann), und Axelrod (1984), *The Evolution of Cooperation*, Basic
Books; Beaufils, Delahaye und Mathieu, *Our meeting with Gradual: a good strategy for the iterated prisoner's dilemma*, Artificial Life V
(Proceedings 1996/1997); Harper, Knight, Jones, Koutsovoulos, Glynatsi und Campbell (2017), *Reinforcement learning produces dominant
strategies for the iterated prisoner's dilemma*, PLoS ONE 12(12), e0188046 (trainierte Strategien gegen mehr als 170 Gegner); Knight,
Campbell, Harper, Gaffney und Glynatsi (2025, Preprint arXiv 2510.15438), *Reviving, reproducing, and revisiting Axelrod's second
tournament* (272 Strategien, Rauschen 0, 1 und 5 %; nur Abstract und Abschnitt 4 gelesen, Turnierlänge dort nicht angegeben).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
