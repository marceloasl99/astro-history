"""
Alvos históricos mensais para o hindcast e o forecast (v3).

Fontes objetivas (não curadas em retrospecto):
- events_v2 (SQLite): catálogo objetivo do projeto (UCDP, COW, NBER, Powell & Thyne, Polity5), 1800–2025.
- COW Inter-State War Data v4.0 (data/external/Inter-StateWarData_v4.0.csv): inícios de guerras interestatais 1816–2007.
- NBER (data/external/business_cycle_dates.json): meses de recessão nos EUA desde 1854.
- UCDP/PRIO Armed Conflict Dataset v24.1 (data/external/UcdpPrioConflict_v24_1.csv): novos episódios de conflito 1946–2023.

Cada alvo informa sua cobertura temporal; o hindcast só avalia dentro dela.
O catálogo de 300 eventos (curado) fica fora do treino — é usado apenas para exibição.
"""

import csv
import json
import os
import sqlite3
from collections import defaultdict
from typing import Dict, Any, Tuple, List

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXTERNAL = os.path.join(ROOT, "data", "external")
DB_PATH = os.path.join(ROOT, "db", "history_astrology.db")


def _month_key(y: int, m: int) -> int:
    return y * 12 + (m - 1)


class MonthlyTargets:
    def __init__(self, start_year: int = 1750, end_year: int = 2150):
        self.start_year, self.end_year = start_year, end_year
        self.months = np.array([(y, m) for y in range(start_year, end_year + 1) for m in range(1, 13)], dtype=np.int32)
        self.keys = self.months[:, 0].astype(np.int64) * 12 + (self.months[:, 1] - 1)
        self.n = len(self.months)
        self.targets: Dict[str, np.ndarray] = {}
        self.coverage: Dict[str, Tuple[int, int]] = {}
        self.kind: Dict[str, str] = {}
        self.description: Dict[str, str] = {}

    def _idx(self, y: int, m: int) -> int:
        k = _month_key(y, m)
        i = int(k - self.keys[0])
        return i if 0 <= i < self.n else -1

    def add(self, name: str, values: np.ndarray, coverage: Tuple[int, int], kind: str, description: str):
        self.targets[name] = values.astype(np.float32)
        self.coverage[name] = coverage
        self.kind[name] = kind
        self.description[name] = description

    def mask(self, name: str) -> np.ndarray:
        y0, y1 = self.coverage[name]
        return (self.months[:, 0] >= y0) & (self.months[:, 0] <= y1)

    # ---------------------------------------------------------------- fontes
    def load_events_v2(self):
        if not os.path.exists(DB_PATH):
            return
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("""
            SELECT event_class, event_date FROM events_v2
            WHERE date_precision IN ('day','month') AND event_date >= '1800-01-01' AND event_date <= '2025-12-31'
        """).fetchall()
        conn.close()
        per_class: Dict[str, np.ndarray] = defaultdict(lambda: np.zeros(self.n))
        any_ev = np.zeros(self.n)
        for cls, d in rows:
            y, m = int(d[:4]), int(d[5:7])
            i = self._idx(y, m)
            if i >= 0:
                per_class[cls][i] = 1.0
                any_ev[i] = 1.0
        self.add("v2_any", any_ev, (1800, 2025), "binary", "Catálogo objetivo v2: mês com ≥1 evento (todas as classes)")
        for cls, arr in per_class.items():
            self.add(f"v2_{cls}", arr, (1800, 2025), "binary", f"Catálogo objetivo v2: mês com evento da classe {cls}")

    def load_cow_wars(self):
        path = os.path.join(EXTERNAL, "Inter-StateWarData_v4.0.csv")
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
            text = f.read().replace("\r\n", "\n").replace("\r", "\n")
        reader = csv.DictReader(text.splitlines())
        wars: Dict[str, Dict[str, Any]] = {}
        for r in reader:
            try:
                w = r["WarNum"]
                sy, sm = int(r["StartYear1"]), int(r["StartMonth1"])
                ey, em = int(r["EndYear1"]), int(r["EndMonth1"])
                if int(r["EndYear2"]) > 0:
                    ey, em = int(r["EndYear2"]), int(r["EndMonth2"])
                deaths = max(0, int(r["BatDeath"]))
            except (ValueError, KeyError):
                continue
            if sy <= 0 or sm <= 0:
                continue
            cur = wars.setdefault(w, {"start": (sy, sm), "end": (ey, em), "deaths": 0})
            cur["start"] = min(cur["start"], (sy, sm))
            if ey > 0:
                cur["end"] = max(cur["end"], (ey, em))
            cur["deaths"] += deaths
        onset = np.zeros(self.n)
        ongoing = np.zeros(self.n)
        severity = np.zeros(self.n)
        for w in wars.values():
            i = self._idx(*w["start"])
            if i >= 0:
                onset[i] += 1
                severity[i] += np.log10(1 + w["deaths"])
            j = self._idx(*w["end"]) if w["end"][0] > 0 else i
            if i >= 0 and j >= i:
                ongoing[i:j + 1] = 1.0
        self.add("cow_war_onset", (onset > 0).astype(float), (1816, 2007), "binary", "COW v4: mês com início de guerra interestatal")
        self.add("cow_war_onset_count", onset, (1816, 2007), "count", "COW v4: nº de guerras interestatais iniciadas no mês")
        self.add("cow_war_ongoing", ongoing, (1816, 2007), "binary", "COW v4: guerra interestatal em curso no mês")
        self.add("cow_war_severity", severity, (1816, 2007), "continuous", "COW v4: log10(1+mortes em batalha) das guerras iniciadas no mês")

    def load_nber(self):
        path = os.path.join(EXTERNAL, "business_cycle_dates.json")
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            cycles = json.load(f)
        rec = np.zeros(self.n)
        start = np.zeros(self.n)
        for c in cycles:
            if not c.get("peak") or not c.get("trough"):
                continue
            py, pm = int(c["peak"][:4]), int(c["peak"][5:7])
            ty, tm = int(c["trough"][:4]), int(c["trough"][5:7])
            i, j = self._idx(py, pm), self._idx(ty, tm)
            if i >= 0 and j >= i:
                rec[i + 1:j + 1] = 1.0  # recessão: do mês seguinte ao pico até o vale
                start[i + 1] = 1.0
        self.add("nber_recession", rec, (1857, 2024), "binary", "NBER: mês em recessão (EUA)")
        self.add("nber_recession_start", start, (1857, 2024), "binary", "NBER: mês de início de recessão (EUA)")

    def load_ucdp(self):
        path = os.path.join(EXTERNAL, "UcdpPrioConflict_v24_1.csv")
        if not os.path.exists(path):
            return
        onsets_all = np.zeros(self.n)
        onsets_inter = np.zeros(self.n)
        war_years: Dict[int, int] = defaultdict(int)
        seen = set()
        with open(path, "r", encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                try:
                    key = (r["conflict_id"], r["start_date2"])
                    if key not in seen:
                        seen.add(key)
                        y, m = int(r["start_date2"][:4]), int(r["start_date2"][5:7])
                        i = self._idx(y, m)
                        if i >= 0:
                            onsets_all[i] += 1
                            if r["type_of_conflict"] == "2":
                                onsets_inter[i] += 1
                    if r["intensity_level"] == "2":
                        war_years[int(r["year"])] += 1
                except (ValueError, KeyError):
                    continue
        wars_month = np.zeros(self.n)
        for y, cnt in war_years.items():
            for m in range(1, 13):
                i = self._idx(y, m)
                if i >= 0:
                    wars_month[i] = cnt
        self.add("ucdp_onset_any", (onsets_all > 0).astype(float), (1946, 2023), "binary", "UCDP/PRIO: mês com início de episódio de conflito armado")
        self.add("ucdp_onset_count", onsets_all, (1946, 2023), "count", "UCDP/PRIO: nº de episódios de conflito iniciados no mês")
        self.add("ucdp_onset_interstate", (onsets_inter > 0).astype(float), (1946, 2023), "binary", "UCDP/PRIO: mês com início de conflito interestatal")
        self.add("ucdp_wars_active", wars_month, (1946, 2023), "count", "UCDP/PRIO: nº de conflitos com ≥1000 mortes no ano")

    def load_all(self) -> "MonthlyTargets":
        self.load_events_v2()
        self.load_cow_wars()
        self.load_nber()
        self.load_ucdp()
        return self

    def summary(self) -> List[Dict[str, Any]]:
        out = []
        for name, arr in self.targets.items():
            m = self.mask(name)
            out.append({
                "target": name, "kind": self.kind[name], "coverage": self.coverage[name],
                "months": int(m.sum()), "positive_months": int((arr[m] > 0).sum()),
                "base_rate": round(float((arr[m] > 0).mean()), 4) if m.any() else None,
                "description": self.description[name],
            })
        return out


def monthly_targets(start_year: int = 1750, end_year: int = 2150) -> MonthlyTargets:
    return MonthlyTargets(start_year, end_year).load_all()


if __name__ == "__main__":
    t = monthly_targets()
    for s in t.summary():
        print(f"{s['target']:28s} {s['kind']:10s} {s['coverage']}  meses={s['months']:5d}  positivos={s['positive_months']:4d}  taxa-base={s['base_rate']}")
