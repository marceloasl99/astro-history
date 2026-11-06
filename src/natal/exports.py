"""Exportações do módulo pessoal: CSV (janelas e passagens), ICS (calendário) e JSON."""

import csv
import hashlib
import io
import json
from typing import Any, Dict, List

PRODID = "-//AstroHistory//Trânsitos de Vida v6//PT"


def windows_csv(windows: List[Dict[str, Any]]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "transit_body", "aspect", "natal_point", "start", "end", "duration_days", "n_passes",
                "exact_dates", "orb_max", "tone", "process", "primary_domain", "intensity_peak", "age_start", "age_end",
                "cycle_label", "episode_id", "target_mode"])
    for x in windows:
        w.writerow([x["id"], x["transit_body"], x["aspect"], x["natal_point"], x["start"], x["end"], x["duration_days"],
                    x["n_passes"], ";".join(h["date"] + ("R" if h["retrograde"] else "") for h in x["hits"]),
                    x["orb_max"], x.get("tone", ""), x.get("process", ""), x.get("primary_domain", ""),
                    x.get("intensity_peak", ""), x["age_start"], x["age_end"], x.get("cycle_label") or "",
                    x.get("episode_id", ""), x["target_mode"]])
    return buf.getvalue()


def hits_csv(windows: List[Dict[str, Any]]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["window_id", "transit_body", "aspect", "natal_point", "date", "datetime_ut", "retrograde", "age"])
    for x in windows:
        for h in x["hits"]:
            w.writerow([x["id"], x["transit_body"], x["aspect"], x["natal_point"], h["date"], h["datetime_ut"],
                        "R" if h["retrograde"] else "D", h["age"]])
    return buf.getvalue()


def _fold(line: str) -> str:
    out, cur = [], ""
    for ch in line:
        if len((cur + ch).encode("utf-8")) > 72:
            out.append(cur)
            cur = " " + ch
        else:
            cur += ch
    out.append(cur)
    return "\r\n".join(out)


def _esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def ics_calendar(windows: List[Dict[str, Any]], label: str = "", include_windows: bool = False,
                 min_intensity: float = 0.0, lang: str = "pt") -> str:
    """Passagens exatas como eventos de dia inteiro; opcionalmente as janelas de corpos lentos como eventos multi-dia."""
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:{PRODID}", "CALSCALE:GREGORIAN",
             _fold(f"X-WR-CALNAME:{_esc(('Trânsitos de Vida' if lang == 'pt' else 'Life Transits') + (' — ' + label if label else ''))}")]
    for w in windows:
        if w.get("intensity_peak", 1.0) < min_intensity or w.get("transit_body") == "moon":
            continue
        summary = f"{w['transit_symbol']} {w['aspect_symbol']} {w['point_symbol']} — {w['transit_name']} {w['aspect_name']} {w['point_name']}"
        if w.get("cycle_label"):
            summary += f" · {w['cycle_label']}"
        desc = (f"{'Janela' if lang == 'pt' else 'Window'}: {w['start']} → {w['end']} · "
                f"{'passagens' if lang == 'pt' else 'passes'}: {w['n_passes']} · orbe ≤ {w['orb_max']}°")
        for h in w["hits"]:
            uid = hashlib.sha1(f"{w['id']}|{h['date']}".encode()).hexdigest()[:24] + "@astrohistory"
            d = h["date"].replace("-", "")
            nxt = _next_day(h["date"])
            lines += ["BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:19700101T000000Z", f"DTSTART;VALUE=DATE:{d}",
                      f"DTEND;VALUE=DATE:{nxt}", _fold("SUMMARY:" + _esc(summary + (" (℞)" if h["retrograde"] else ""))),
                      _fold("DESCRIPTION:" + _esc(desc + f" · {'exato' if lang == 'pt' else 'exact'}: {h['datetime_ut']}")),
                      "END:VEVENT"]
        if include_windows and w["duration_days"] >= 20:
            uid = hashlib.sha1(f"{w['id']}|window".encode()).hexdigest()[:24] + "@astrohistory"
            lines += ["BEGIN:VEVENT", f"UID:{uid}", "DTSTAMP:19700101T000000Z",
                      f"DTSTART;VALUE=DATE:{w['start'].replace('-', '')}", f"DTEND;VALUE=DATE:{_next_day(w['end'])}",
                      _fold("SUMMARY:" + _esc(("Janela: " if lang == "pt" else "Window: ") + summary)),
                      _fold("DESCRIPTION:" + _esc(desc)), "TRANSP:TRANSPARENT", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def _next_day(iso: str) -> str:
    from datetime import date, timedelta
    y, m, d = (int(x) for x in iso[:10].split("-"))
    return (date(y, m, d) + timedelta(days=1)).strftime("%Y%m%d")


def to_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=_default)


def _default(o):
    try:
        import numpy as np
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, (np.floating, np.integer)):
            return o.item()
    except Exception:
        pass
    return str(o)
