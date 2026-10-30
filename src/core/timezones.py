"""
Conversão de hora local → Tempo Universal com fuso horário histórico real.

Regras:
- A partir de 1883 (adoção dos fusos padrão): zona IANA resolvida por lat/lon
  (timezonefinder + zoneinfo), incluindo horário de verão histórico.
- Antes de 1883, ou sem coordenadas, ou em alto-mar: Hora Média Local exata
  (longitude / 15, sem arredondar).
- A data pode mudar na conversão (ex.: 23:00 em Nova York = 04:00 UT do dia seguinte);
  o resultado traz a data UT corrigida.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

STANDARD_TIME_START_YEAR = 1883

_TZ_FINDER = None


def _finder():
    global _TZ_FINDER
    if _TZ_FINDER is None:
        try:
            from timezonefinder import TimezoneFinder
            _TZ_FINDER = TimezoneFinder(in_memory=True)
        except Exception as e:  # pragma: no cover - dependência opcional
            logger.warning("timezonefinder indisponível (%s); usando Hora Média Local.", e)
            _TZ_FINDER = False
    return _TZ_FINDER or None


def resolve_zone(latitude: Optional[float], longitude: Optional[float]) -> Optional[str]:
    if latitude is None or longitude is None:
        return None
    tf = _finder()
    if tf is None:
        return None
    try:
        return tf.timezone_at(lat=float(latitude), lng=float(longitude))
    except Exception:
        return None


def local_to_ut(
    year: int, month: int, day: int, local_hour: float,
    latitude: Optional[float] = None, longitude: Optional[float] = None
) -> Dict[str, Any]:
    """
    Retorna {"year","month","day","ut_hour","tz_source","utc_offset_hours"} com a data UT
    já ajustada quando a conversão cruza a meia-noite.
    """
    lon = float(longitude) if longitude is not None else 0.0
    zone = resolve_zone(latitude, longitude) if year >= STANDARD_TIME_START_YEAR else None

    if zone and 1 <= year <= 9999:
        try:
            h = int(local_hour)
            m = int(round((local_hour - h) * 60.0))
            if m >= 60:
                h, m = h + 1, m - 60
            local_dt = datetime(year, month, day, 0, 0, tzinfo=ZoneInfo(zone)) + timedelta(hours=h, minutes=m)
            ut_dt = local_dt.astimezone(timezone.utc)
            offset = local_dt.utcoffset().total_seconds() / 3600.0
            return {
                "year": ut_dt.year, "month": ut_dt.month, "day": ut_dt.day,
                "ut_hour": ut_dt.hour + ut_dt.minute / 60.0 + ut_dt.second / 3600.0,
                "tz_source": f"iana:{zone}",
                "utc_offset_hours": round(offset, 3),
            }
        except Exception as e:
            logger.warning("Falha ao aplicar zona %s: %s; usando LMT.", zone, e)

    # Hora Média Local exata
    offset = lon / 15.0
    ut_hour = local_hour - offset
    day_shift = 0
    while ut_hour < 0.0:
        ut_hour += 24.0
        day_shift -= 1
    while ut_hour >= 24.0:
        ut_hour -= 24.0
        day_shift += 1
    y, mo, d = year, month, day
    if day_shift != 0:
        y, mo, d = _shift_civil_date(year, month, day, day_shift)
    return {
        "year": y, "month": mo, "day": d, "ut_hour": ut_hour,
        "tz_source": "lmt",
        "utc_offset_hours": round(offset, 3),
    }


def _shift_civil_date(year: int, month: int, day: int, days: int):
    """Desloca a data civil em `days` sem passar pelo datetime (suporta anos <= 0 e calendário juliano aproximado)."""
    try:
        dt = datetime(year, month, day) + timedelta(days=days)
        return dt.year, dt.month, dt.day
    except (ValueError, OverflowError):
        import swisseph as swe
        jd = swe.julday(year, month, day, 0.0) + days
        y, m, d, _ = swe.revjul(jd)
        return y, m, d
