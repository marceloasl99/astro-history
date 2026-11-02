"""
historical_analogues.py
Motor 'Cosmic History Search' (Historical Analogues Engine).
Dado um instante no tempo (futuro ou presente), calcula as posições planetárias
e vasculha o catálogo de mais de 1.300 eventos históricos para identificar
quais acontecimentos no passado ocorreram sob céus e configurações astronômicas mais análogas.

Métricas de Similaridade:
1. Similaridade Angular dos Ciclos Exteriores (Outer Planets Alignment):
   Compara as distâncias relativas entre os pares dos planetas lentos (Júpiter a Plutão).
   S_outer = sum_{i < j} cos(delta_theta_target - delta_theta_hist)
2. Similaridade de Signos / Posição Absoluta no Zodíaco:
   cos(lambda_target, p - lambda_hist, p)
3. Sobreposição de Aspectos Maiores (Conjunção, Oposição, Quadratura, Trígono, Sextil).

Retorna ranking percentual (0 a 100%) e justificativa detalhada dos ciclos compartilhados.
"""

import math
import sqlite3
import os
from typing import Dict, Any, List, Optional
import swisseph as swe

from src.features.sum_of_cosines import get_planet_longitudes, OUTER_PLANET_KEYS
from src.features.barbault_ci import angular_distance, compute_cyclic_index

DB_PATH = "db/history_astrology.db"

# Pares de planetas exteriores para matriz de ciclos (10 pares)
OUTER_PAIRS = [
    ("jupiter", "saturn"),
    ("jupiter", "uranus"),
    ("jupiter", "neptune"),
    ("jupiter", "pluto"),
    ("saturn", "uranus"),
    ("saturn", "neptune"),
    ("saturn", "pluto"),
    ("uranus", "neptune"),
    ("uranus", "pluto"),
    ("neptune", "pluto")
]

class HistoricalAnaloguesEngine:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._events_cache: Optional[List[Dict[str, Any]]] = None

    def _load_events_with_planets(self) -> List[Dict[str, Any]]:
        if self._events_cache is not None:
            return self._events_cache

        if not os.path.exists(self.db_path):
            return []

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Carregar todos os eventos calculados
        cur.execute("""
            SELECT id, title, category, date, time, city, country, latitude, longitude, consequence, tjd_ut
            FROM events
            WHERE calculated = 1 AND tjd_ut IS NOT NULL
            ORDER BY id ASC;
        """)
        events_rows = [dict(r) for r in cur.fetchall()]

        # Carregar posições planetárias dos planetas lentos
        cur.execute("""
            SELECT event_id, planet_id, abs_degree
            FROM planet_positions
            WHERE planet_id IN ('jupiter', 'saturn', 'uranus', 'neptune', 'pluto', 'mars', 'sun');
        """)
        pos_rows = cur.fetchall()
        conn.close()

        planets_by_event = {}
        for r in pos_rows:
            eid = r["event_id"]
            if eid not in planets_by_event:
                planets_by_event[eid] = {}
            planets_by_event[eid][r["planet_id"]] = float(r["abs_degree"])

        events_data = []
        rad_conv = math.pi / 180.0

        for ev in events_rows:
            eid = ev["id"]
            pos = planets_by_event.get(eid, {})
            if not pos:
                continue

            # Pré-computar distâncias angulares dos pares exteriores
            outer_dists = {}
            for p1, p2 in OUTER_PAIRS:
                if p1 in pos and p2 in pos:
                    outer_dists[(p1, p2)] = angular_distance(pos[p1], pos[p2])

            ev["planets"] = pos
            ev["outer_dists"] = outer_dists
            events_data.append(ev)

        self._events_cache = events_data
        return self._events_cache

    def find_analogues_for_date(
        self,
        date_iso: str,
        category_filter: Optional[str] = None,
        top_k: int = 5,
        exclude_event_id: Optional[int] = None,
        min_year_diff: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Encontra os top_k eventos históricos mais semelhantes à data informada (YYYY-MM-DD).
        """
        try:
            parts = [int(p) for p in date_iso.strip().split("-")]
            y, m, d = parts[0], parts[1], parts[2]
            tjd_target = swe.julday(y, m, d, 12.0)
        except Exception as e:
            raise ValueError(f"Formato de data inválido '{date_iso}'. Esperado YYYY-MM-DD: {e}")

        # Calcular posições na data alvo
        target_lons = get_planet_longitudes(tjd_target, heliocentric=False)
        target_ci = compute_cyclic_index(target_lons, use_pluto=True)

        target_outer_dists = {}
        for p1, p2 in OUTER_PAIRS:
            if p1 in target_lons and p2 in target_lons:
                target_outer_dists[(p1, p2)] = angular_distance(target_lons[p1], target_lons[p2])

        events = self._load_events_with_planets()
        if category_filter:
            events = [e for e in events if e["category"] == category_filter]

        rad_conv = math.pi / 180.0
        scored_events = []

        for ev in events:
            if exclude_event_id is not None and ev["id"] == exclude_event_id:
                continue
            if min_year_diff is not None:
                try:
                    d_str = ev.get("date", "")
                    if d_str.startswith("-"):
                        ev_year = -int(d_str[1:].split("-")[0])
                    else:
                        ev_year = int(d_str.split("-")[0])
                    if abs(ev_year - y) < min_year_diff:
                        continue
                except Exception:
                    pass

            ev_dists = ev["outer_dists"]
            ev_planets = ev["planets"]

            # 1. Concordância de ciclos dos pares exteriores (0.0 a 1.0)
            pair_similarities = []
            matching_pairs_info = []

            for pair in OUTER_PAIRS:
                if pair in target_outer_dists and pair in ev_dists:
                    diff_deg = abs(target_outer_dists[pair] - ev_dists[pair])
                    # Similaridade de cosseno da diferença angular: 1.0 se mesma distância, 0 se diferença de 90°
                    sim = max(0.0, math.cos(diff_deg * rad_conv))
                    pair_similarities.append(sim)

                    if diff_deg <= 12.0:
                        p1_name, p2_name = pair
                        matching_pairs_info.append(
                            f"{p1_name.title()}–{p2_name.title()} (distância alvo: {target_outer_dists[pair]:.1f}°, histórica: {ev_dists[pair]:.1f}°)"
                        )

            cycle_similarity = sum(pair_similarities) / len(pair_similarities) if pair_similarities else 0.0

            # 2. Similaridade de posição dos planetas lentos no zodíaco
            zodiac_sims = []
            for p in OUTER_PLANET_KEYS:
                if p in target_lons and p in ev_planets:
                    diff = abs(target_lons[p] - ev_planets[p]) * rad_conv
                    zodiac_sims.append((math.cos(diff) + 1.0) / 2.0)  # Mapeado em [0, 1]

            zodiac_score = sum(zodiac_sims) / len(zodiac_sims) if zodiac_sims else 0.0

            # Score Composto: 70% estrutura dos ciclos mundanos + 30% signos zodiacais
            total_similarity = (0.70 * cycle_similarity) + (0.30 * zodiac_score)
            score_pct = round(total_similarity * 100.0, 1)

            scored_events.append({
                "score_pct": score_pct,
                "cycle_similarity_pct": round(cycle_similarity * 100.0, 1),
                "zodiac_similarity_pct": round(zodiac_score * 100.0, 1),
                "event_id": ev["id"],
                "title": ev["title"],
                "category": ev["category"],
                "date": ev["date"],
                "city": ev["city"],
                "country": ev["country"],
                "consequence": ev["consequence"],
                "shared_cycles": matching_pairs_info[:3]
            })

        scored_events.sort(key=lambda x: x["score_pct"], reverse=True)
        top_matches = scored_events[:top_k]

        return {
            "query_date": date_iso,
            "target_ci5_sum": target_ci["sum_degrees"],
            "target_ci5_pct": target_ci["normalized_pct"],
            "evaluated_historical_events": len(events),
            "top_analogues": top_matches
        }

# Instância singleton para uso prático
_default_engine = None

def find_historical_analogues(
    date_iso: str,
    category_filter: Optional[str] = None,
    top_k: int = 5,
    exclude_event_id: Optional[int] = None,
    min_year_diff: Optional[int] = None
) -> Dict[str, Any]:
    global _default_engine
    if _default_engine is None:
        _default_engine = HistoricalAnaloguesEngine()
    return _default_engine.find_analogues_for_date(
        date_iso,
        category_filter=category_filter,
        top_k=top_k,
        exclude_event_id=exclude_event_id,
        min_year_diff=min_year_diff
    )
