import sqlite3
import json
import numpy as np
from collections import defaultdict

DB_PATH = "archive/v0/history_astrology.db"
OUTPUT_PATH = "reports/baseline_metrics.json"

def compute():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    rows = c.execute("""
        SELECT id, title, category, date, tension_index, chart_json
        FROM events
        ORDER BY date ASC
    """).fetchall()

    scores_all = []
    scores_by_cat = defaultdict(list)
    scores_by_era = defaultdict(list)
    star_counts = []
    star_freq = defaultdict(int)
    aspect_counts = []

    ceiling_990_count = 0
    ceiling_sub_indices = {"conflict_990": 0, "crisis_990": 0}

    for r in rows:
        ev_id, title, cat, dt, tension, chart_raw = r
        year = int(dt.split("-")[0]) if not dt.startswith("-") else -int(dt.split("-")[1])
        
        era = "Antiguidade / Medieval (<1500)" if year < 1500 else \
              "Moderna (1500-1799)" if year < 1800 else \
              "Século XIX (1800-1899)" if year < 1900 else \
              "Século XX (1900-1999)" if year < 2000 else \
              "Século XXI (2000-2025)"

        chart = json.loads(chart_raw) if chart_raw else {}
        summary = chart.get("summary", {})
        sub_indices = summary.get("sub_indices_1000", {})
        t_1000 = summary.get("tension_index_1000", tension)
        
        scores_all.append(t_1000)
        scores_by_cat[cat].append(t_1000)
        scores_by_era[era].append(t_1000)

        if t_1000 >= 990.0:
            ceiling_990_count += 1
        if sub_indices.get("conflict_risk_index_1000", 0.0) >= 990.0:
            ceiling_sub_indices["conflict_990"] += 1
        if sub_indices.get("crisis_risk_index_1000", 0.0) >= 990.0:
            ceiling_sub_indices["crisis_990"] += 1

        stars = chart.get("star_contacts", [])
        star_counts.append(len(stars))
        for s in stars:
            star_freq[s.get("star_key", s.get("star_name"))] += 1

        aspects = chart.get("aspects", [])
        aspect_counts.append(len(aspects))

    conn.close()

    scores_arr = np.array(scores_all)

    def stats_dict(arr):
        return {
            "count": len(arr),
            "mean": round(float(np.mean(arr)), 2),
            "std": round(float(np.std(arr, ddof=1)), 2) if len(arr) > 1 else 0.0,
            "min": round(float(np.min(arr)), 2),
            "p25": round(float(np.percentile(arr, 25)), 2),
            "median": round(float(np.median(arr)), 2),
            "p75": round(float(np.percentile(arr, 75)), 2),
            "p90": round(float(np.percentile(arr, 90)), 2),
            "max": round(float(np.max(arr)), 2)
        }

    category_stats = {cat: stats_dict(sc) for cat, sc in scores_by_cat.items()}
    era_stats = {era: stats_dict(sc) for era, sc in scores_by_era.items()}

    hist_counts, hist_bins = np.histogram(scores_arr, bins=10, range=(0, 1000))
    histogram = [
        {"bin_start": round(float(hist_bins[i]), 1),
         "bin_end": round(float(hist_bins[i+1]), 1),
         "count": int(hist_counts[i])}
        for i in range(len(hist_counts))
    ]

    top_stars = sorted(star_freq.items(), key=lambda x: x[1], reverse=True)[:10]

    baseline = {
        "dataset_name": "historical_events_v0",
        "total_events": len(rows),
        "overall_score_stats": stats_dict(scores_arr),
        "saturation": {
            "events_tension_ge_990": ceiling_990_count,
            "events_conflict_ge_990": ceiling_sub_indices["conflict_990"],
            "events_crisis_ge_990": ceiling_sub_indices["crisis_990"],
        },
        "star_contacts_stats": {
            "total_star_contacts": sum(star_counts),
            "mean_per_chart": round(float(np.mean(star_counts)), 2),
            "std_per_chart": round(float(np.std(star_counts, ddof=1)), 2),
            "top_10_stars": [{"star": k, "hits": v} for k, v in top_stars]
        },
        "aspect_stats": {
            "total_aspects": sum(aspect_counts),
            "mean_per_chart": round(float(np.mean(aspect_counts)), 2)
        },
        "category_stats": category_stats,
        "era_stats": era_stats,
        "histogram": histogram
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(baseline, f, indent=2, ensure_ascii=False)

    print(f"Baseline metrics saved to {OUTPUT_PATH}")
    print(f"Overall tension mean: {baseline['overall_score_stats']['mean']}, std: {baseline['overall_score_stats']['std']}")
    print(f"Total star contacts: {baseline['star_contacts_stats']['total_star_contacts']}, Mean per chart: {baseline['star_contacts_stats']['mean_per_chart']}")
    print(f"Saturations in 990 (Tension: {ceiling_990_count}, Conflict: {ceiling_sub_indices['conflict_990']}, Crisis: {ceiling_sub_indices['crisis_990']})")

if __name__ == "__main__":
    compute()
