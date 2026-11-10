# Axelrod-Turnier: wer gewinnt, hängt am Feld – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-axelrod-turnier-demo.streamlit.app/)**

Zweites Stück der **Wiederholte-Spiele-Linie** in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“.
Nachfolger von [tit-for-tat-demo](https://sebastianhanisch-tit-for-tat-demo.streamlit.app/): dort ging es um die Frage, ab welchem Diskontfaktor Vergeltung Kooperation stabil hält,
hier um das **Abschneiden im Feld**: 16 klassische Strategien spielen im wiederholten Gefangenendilemma jeder gegen jeden. Die Kante ist ein `fix`: Stück 1 prüft ein Paar
exakt, sagt aber nichts darüber, wie eine Strategie gegen eine ganze Gegnermenge abschneidet.

Vehikel: das Gefangenendilemma aus Stück 1 mit den klassischen Auszahlungen 5/3/1/0 (nur nutzen / beide tauschen / keiner tauscht / angeboten, nichts bekommen). Die Auszahlungen sind
hier fest; Eigennutz und Rationalität sind Modellannahmen.

## Warum dieses Problem

Axelrods Turnier (1980) gilt als Beleg dafür, dass Tit-for-Tat „die beste Strategie“ ist. Ein Turnier misst aber nur, wie eine Strategie gegen **die gerade angetretenen** Gegner
abschneidet. Die Demo fragt: Wie viel vom Ergebnis steckt im Feld, im Rauschen und im Training?

## Modell

16 Strategien (Immer kooperieren, Immer defektieren, Tit-for-Tat, Misstrauisches Tit-for-Tat, Grim Trigger, Tit-for-Two-Tats, Hartes Tit-for-Tat, Pavlov, Joss, Großzügiges
Tit-for-Tat, Naiver Prober, Zufall, Abwechsler, Davis, Gradual, Rüpel) und eine trainierte Tabelle. Jedes Paar spielt 20 Wiederholungen über 50 bis 500 Runden (Voreinstellung 200),
optional mit Rauschen (die ausgeführte Aktion ist mit Wahrscheinlichkeit ε die andere als die beabsichtigte; beide sehen die ausgeführte). Die **Wertung** ist die mittlere
Auszahlung je Runde gegen alle **anderen** Teilnehmer; ein Gleichstand teilt den Rang. Die App erklärt alle 16 Strategien in einer Tabelle, mit ihren eigenen ersten zwölf
Aktionen gegen Immer-D und gegen einen Abwechsler.

## Methodik

- **Matrix:** `payoff_matrix`: jede Zelle hängt nur von ihren zwei Strategien und dem Turnier-Seed ab, nicht von der Position im Feld. Ein Teilfeld-Turnier ist deshalb exakt ein Ausschnitt
  der Gesamtmatrix.
- **Teilfelder:** 2000 zufällige 8er-Teilfelder, Tit-for-Tat immer dabei: Rang von Tit-for-Tat und Sieger je Teilfeld (`subfield_outcomes`).
- **Rauschen:** dieselbe Matrix bei 0, 1 und 5 %.
- **Trainierte Tabelle:** 18 Bits (Kontext aus den letzten zwei Runden beider Spieler plus zwei Startzüge), Hill-Climbing gegen die Trainingsgegner; 20 Aufteilungen in je 10
  Trainings- und 6 Testgegner sind vorgerechnet (`tools/precompute.py`, `axt_data.json`).

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen: 200 Runden, 20 Wiederholungen, Seed 20260, sofern nicht anders genannt.

| Frage | Befund | Test |
|---|---|---|
| Gewinnt Tit-for-Tat das Feld aus 16? | **Nein.** Rang 6 von 16 (2,46 Punkte je Runde); es gewinnt Gradual mit 2,76, dahinter Grim Trigger, Davis, Großzügiges Tit-for-Tat, Tit-for-Two-Tats. | `test_default_field_ranking_and_tft_position` |
| Gewinnt es wenigstens einzelne Spiele? | **Nein, nie, ohne Rauschen:** gegen keinen der 16 erzielt es mehr Punkte als der Gegner. Das ist kein Zufall, sondern folgt aus dem Spiegeln (Beweis im 📐-Expander). | `test_tft_wins_no_single_match_without_noise`, `test_tft_never_scores_more_than_its_opponent_without_noise` |
| Wie stabil ist das über Teilfelder? | In 4,9 % der 8er-Teilfelder gewinnt Tit-for-Tat, im Median belegt es Rang 3 von 8; am häufigsten gewinnt Gradual (29 %). | `test_subfield_statistics_at_zero_noise` |
| Was ändert Rauschen? | Rang von Tit-for-Tat bei 0 / 1 / 5 %: 6 / 6 / 7 von 16; Gradual gewinnt bei allen drei Stufen. Bei 5 % liegen Grim Trigger und Immer-Defektieren auf den Plätzen 2 und 3. | `test_tft_rank_over_the_noise_levels` |
| Nur nette Strategien, ohne Fehler? | Alle neun erzielen genau 3,00: ein Neunfach-Gleichstand um Rang 1, nichts zu entscheiden. Mit 1 % Rauschen gewinnt Großzügiges Tit-for-Tat, Tit-for-Tat belegt Rang 4 von 9. | `test_nothing_to_decide_among_the_nice_strategies_without_noise`, `test_nice_strategies_with_one_percent_noise_tft_is_fourth_of_nine` |
| Böse Mehrheit (7 bösartige + Tit-for-Tat, Immer-Kooperieren, Grim)? | Grim Trigger gewinnt, Tit-for-Tat Rang 4 von 10 (2,10). | `test_nasty_majority_grim_wins_and_tft_is_fourth_of_ten` |
| Hilft Training gegen ein Feld? | Gegen die Trainingsgegner schlägt die Tabelle Tit-for-Tat in 19 von 20 Aufteilungen (im Mittel +0,43 Punkte je Runde), gegen **ungesehene** nur in 14 von 20 (im Mittel +0,16, im schlechtesten Fall −0,45). | `test_split_summary_numbers`, `test_precomputed_splits_are_reproducible` |
| Und im eigenen Trainingsfeld? | Die auf alle 16 trainierte Tabelle gewinnt das Feld (Tit-for-Tat Rang 7 von 17): kein Beleg für Stärke, sie kennt ihre Gegner. | `test_trained_table_wins_its_own_training_field` |

### Korrektur gegenüber dem Plan

Der Plan der Linie erwartete „Tit-for-Tat gewinnt im Originalfeld, fällt aber im erweiterten Feld zurück“. In **keinem** der hier gebauten Felder gewinnt Tit-for-Tat. Das ist
kein Widerspruch zu Axelrod, sondern eine Aussage über **dieses** Feld: Das Original-Teilnehmerfeld von 1980 ist hier nicht nachgebaut. Der Preprint von Knight et al. (2025) stützt die
Feldabhängigkeit (Tit-for-Tat gewinnt dort die Rekonstruktion des Originalfeldes, im 272er-Feld nicht). Die Demo behauptet deshalb nicht „Tit-for-Tat gewinnt im Original“.
Außerdem hat die erste Einzelmessung der trainierten Tabelle (eine Aufteilung, Tabelle schlechter als Tit-for-Tat auf ungesehenen Gegnern) das Bild überzeichnet: über 20
Aufteilungen schlägt sie Tit-for-Tat auf ungesehenen Gegnern in 14 Fällen und verliert in 6.

## Ehrliche Grenzen

- **Eigenes Feld:** 16 selbst implementierte Strategien nach gängigen Beschreibungen, nicht Axelrods Teilnehmerliste und nicht die Bibliothek mit über 250 Strategien.
- **Wertung:** Mittel gegen alle anderen, ohne Selbstspiel; andere Wertungen (Rangpunkte, Eliminationsrunden, evolutionäre Anteile) können die Reihenfolge ändern.
- **Streuung:** 20 Wiederholungen je Paar, fester Seed; Plätze mit kleinem Abstand wechseln mit dem Seed.
- **Trainierte Tabelle:** kleines Feld, kurzes Training, zwei Runden Gedächtnis. Kein Nachbau der in der Literatur trainierten Strategien (gegen mehr als 170 Gegner).
- **Feste Strategien:** keine Anpassung während des Turniers, keine Population.

## Verifikation

- **Kern:** je Einheit eine Handrechnung (jede der 16 Strategien auf einer festen Gegnerfolge, Spiele, Rangliste auf drei Strategien, Gleichstände, Seed-Unabhängigkeit der
  Paarungsreihenfolge). Der Test „Teilfeld-Turnier = Ausschnitt der Gesamtmatrix“ fand beim Bau einen echten Fehler: die Zufallsfolge eines Paares hing von der Position im Feld ab.
- **Orakel** (`tests/test_oracle_axelrod_turnier.py`): (1) die Simulation gegen die exakte erwartete Auszahlung zweier reaktiver Strategien unter Rauschen (Verteilung über die letzten
  Aktionen); (2) die deterministischen Strategien gegen unabhängig aufgeschriebene Zustandsautomaten auf 40 Zufallsfolgen; (3) die Invariante „Tit-for-Tat gewinnt ohne Rauschen kein
  Spiel“ für alle 16 Gegner und fünf Spiellängen; (4) die Teilfeld-Verteilung gegen Vollaufzählung.
- **Claims:** jede Zahl dieses READMEs in `tests/test_claims.py`, einschließlich Neuberechnung von zwei Aufteilungen und der ausgelieferten Tabelle.
- **Oberfläche:** AppTest (jeder Button, jeder Regler am Minimum und Maximum, Permalink begrenzt und rastet ein, Feld mit einer Strategie zeigt eine Warnung) und Footer-Test.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `axt_algorithm.py` | Kern: Spiel, Matrix, Rangliste mit Gleichständen, Teilfelder |
| `axt_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Presets |
| `axt_data.json` | Vorgerechnet: ausgelieferte Tabelle und 20 Aufteilungen |
| `axt_evaluation.py` | Analyse, Rauschen, Teilfelder, Aufteilungen, Strategieübersicht, Verdikt |
| `axt_presets.py` | Permalink (Begrenzen und Einrasten), Presets |
| `axt_scenario.py` | Auszahlungen und die 16 Strategien |
| `axt_trained.py` | Trainierte Tabelle: Strategie, Hill-Climbing, Laden der Daten |
| `axt_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tools/precompute.py` | Rechnet `axt_data.json` neu |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Handrechnung, Orakel, Claims, Presets, AppTest-Smoke-Test, Footer |

## Bewusst nicht umgesetzt

- **Evolutionäre Dynamik** (Anteile wachsen nach Erfolg, „ökologisches Turnier“): das ist ein eigenes Verfahren mit anderer Aussage, eigenes Stück der Linie.
- **Alle über 250 Bibliotheksstrategien:** das wäre ein Nachbau der Axelrod-Bibliothek; hier steht ein überschaubares Feld, dessen Strategien jede erklärt werden kann.
- **Original-Teilnehmerfeld von 1980:** die Beschreibungen der Einsendungen liegen nicht vollständig vor; die Demo behauptet keine Reproduktion.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit und Plotly.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
