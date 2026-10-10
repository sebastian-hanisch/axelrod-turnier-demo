"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import axt_constants as C
from axt_scenario import CLASSES


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=420, legend=True):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), plot_bgcolor="rgba(0,0,0,0)", showlegend=legend,
                      legend=dict(orientation="h", y=-0.2))
    return lock_axes(fig)


def _color(key: str) -> str:
    if key == "TFT":
        return C.COLOR_TFT
    if key == C.TRAINED_KEY:
        return C.COLOR_TRAINED
    return C.COLOR_NICE if CLASSES[key].nice else C.COLOR_NASTY


def _label(key: str, labels: dict[str, str]) -> str:
    return labels.get(key, key)


def build_ranking(keys, order, scores, labels):
    """Rangliste: Balken je Strategie, beste oben. Blau = Tit-for-Tat, Orange = trainiert, grün = nett, rot = bösartig."""
    names = [labels[keys[i]] for i in order]
    vals = [scores[i] for i in order]
    colors = [_color(keys[i]) for i in order]
    fig = go.Figure(go.Bar(x=vals, y=names, orientation="h", marker_color=colors,
                           text=[f"{v:.2f}".replace(".", ",") for v in vals], textposition="outside",
                           hovertemplate="%{y}: %{x:.3f}<extra></extra>"))
    fig.update_yaxes(autorange="reversed", type="category")
    fig.update_xaxes(title_text="mittlere Auszahlung je Runde gegen die anderen", range=[0, max(vals) * 1.15])
    return _base(fig, height=max(320, 26 * len(keys) + 80), legend=False)


def build_matrix(keys, order, matrix, labels):
    """Auszahlungsmatrix, Zeile gegen Spalte, in Ranglisten-Reihenfolge."""
    names = [labels[keys[i]] for i in order]
    z = [[matrix[i][j] for j in order] for i in order]
    fig = go.Figure(go.Heatmap(z=z, x=names, y=names, zmin=0, zmax=5, colorscale="Teal", xgap=1, ygap=1,
                               hovertemplate="%{y} gegen %{x}: %{z:.2f}<extra></extra>"))
    fig.update_yaxes(autorange="reversed", type="category")
    fig.update_xaxes(type="category", tickangle=-45)
    return _base(fig, height=max(420, 24 * len(keys) + 160), legend=False)


def build_rank_hist(ranks, size):
    counts = [sum(1 for r in ranks if r == k) for k in range(1, size + 1)]
    share = [c / len(ranks) * 100 for c in counts]
    fig = go.Figure(go.Bar(x=[str(k) for k in range(1, size + 1)], y=share, marker_color=C.COLOR_TFT,
                           text=[f"{s:.0f} %" for s in share], textposition="outside",
                           hovertemplate="Rang %{x}: %{y:.1f} %<extra></extra>"))
    fig.update_xaxes(title_text=f"Rang von Tit-for-Tat im {size}er-Teilfeld", type="category")
    fig.update_yaxes(title_text="Anteil der Teilfelder (%)", range=[0, max(share) * 1.2 + 1])
    return _base(fig, height=320, legend=False)


def build_winner_bars(winners, draws, labels):
    items = sorted(winners.items(), key=lambda kv: (-kv[1], kv[0]))
    names = [labels.get(k, k) for k, _ in items]
    share = [v / draws * 100 for _, v in items]
    fig = go.Figure(go.Bar(x=share, y=names, orientation="h", marker_color=[_color(k) for k, _ in items],
                           text=[f"{s:.0f} %" for s in share], textposition="outside",
                           hovertemplate="%{y}: %{x:.1f} % der Teilfelder<extra></extra>"))
    fig.update_yaxes(autorange="reversed", type="category")
    fig.update_xaxes(title_text="Anteil der Teilfelder, die diese Strategie gewinnt (%)", range=[0, max(share) * 1.2 + 1])
    return _base(fig, height=max(240, 30 * len(items) + 90), legend=False)


def build_noise_ranks(ranks_by_level, labels, highlight=("TFT",)):
    """Rang je Strategie über die Rauschstufen; hervorgehoben: `highlight` und der Sieger bei 0 %."""
    levels = list(ranks_by_level)
    keys = list(ranks_by_level[levels[0]])
    fig = go.Figure()
    top0 = min(ranks_by_level[levels[0]], key=ranks_by_level[levels[0]].get)
    for key in keys:
        strong = key in highlight or key == top0
        fig.add_trace(go.Scatter(
            x=[f"{lvl * 100:.0f} %" for lvl in levels], y=[ranks_by_level[lvl][key] for lvl in levels], mode="lines+markers",
            name=_label(key, labels), line=dict(color=_color(key) if strong else C.COLOR_OTHER, width=4 if strong else 1.5),
            marker=dict(size=9 if strong else 5), hovertemplate=_label(key, labels) + ": Rang %{y}<extra></extra>",
            showlegend=strong))
    fig.update_yaxes(autorange="reversed", title_text="Rang", dtick=1)
    fig.update_xaxes(title_text="Rauschen (Wahrscheinlichkeit einer Verwechslung je Aktion)", type="category")
    return _base(fig, height=460)


def build_split_bars(train_diff, test_diff):
    """Vorsprung der trainierten Tabelle vor Tit-for-Tat je Aufteilung: im Training und gegen ungesehene Gegner."""
    idx = [str(i + 1) for i in range(len(train_diff))]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=idx, y=train_diff, name="Trainingsgegner", marker_color=C.COLOR_OTHER,
                         hovertemplate="Aufteilung %{x}: %{y:+.2f}<extra>Training</extra>"))
    fig.add_trace(go.Bar(x=idx, y=test_diff, name="ungesehene Gegner", marker_color=C.COLOR_TRAINED,
                         hovertemplate="Aufteilung %{x}: %{y:+.2f}<extra>Test</extra>"))
    fig.add_hline(y=0, line=dict(color="rgba(60,60,60,0.8)", width=1))
    fig.update_layout(barmode="group")
    fig.update_xaxes(title_text="Aufteilung (10 Trainings-, 6 Testgegner)", type="category")
    fig.update_yaxes(title_text="Vorsprung vor Tit-for-Tat (Punkte je Runde)")
    return _base(fig, height=360)
