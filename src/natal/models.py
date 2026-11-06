"""Modelos de entrada validados do módulo pessoal (Pydantic v2)."""

import hashlib
import json
import re
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from src.natal.bodies import BODY_META, ANGLES, NATAL_BODIES_OPTIONAL, TRANSIT_GRID_BODIES

DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})$")

HouseSystem = Literal["P", "K", "W", "E", "O"]


class BirthInput(BaseModel):
    """Dados de nascimento + opções de cálculo. Tudo vem da URL (stateless)."""

    label: str = Field(default="", max_length=60)
    date: str = Field(..., description="YYYY-MM-DD (gregoriano)")
    time: str = Field(default="12:00", max_length=5)
    time_known: bool = True
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)
    tz: Optional[str] = Field(default=None, max_length=64)
    place: str = Field(default="", max_length=120)
    house_system: HouseSystem = "P"
    orb_preset: Literal["strict", "standard", "wide", "custom"] = "standard"
    orbs: Optional[Dict[str, float]] = None
    bodies: Optional[List[str]] = None       # corpos em trânsito
    targets: Optional[List[str]] = None      # pontos natais alvo
    extra_natal: List[str] = Field(default_factory=list)  # asteroides opcionais na carta
    minors: bool = False
    target_mode: Literal["natal", "progressed"] = "natal"
    range_from: Optional[int] = Field(default=None, ge=1, le=3000)
    range_to: Optional[int] = Field(default=None, ge=1, le=3000)
    focus_year: Optional[int] = Field(default=None, ge=1, le=3000)   # ano em foco para corpos rápidos
    lang: Literal["pt", "en"] = "pt"

    @field_validator("date")
    @classmethod
    def _date_ok(cls, v: str) -> str:
        m = DATE_RE.match(v.strip())
        if not m:
            raise ValueError("data deve estar no formato YYYY-MM-DD")
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if not (1 <= y <= 3000 and 1 <= mo <= 12 and 1 <= d <= 31):
            raise ValueError("data fora do intervalo suportado (anos 1–3000)")
        return f"{y:04d}-{mo:02d}-{d:02d}"

    @field_validator("time")
    @classmethod
    def _time_ok(cls, v: str) -> str:
        m = TIME_RE.match(v.strip())
        if not m:
            raise ValueError("hora deve estar no formato HH:MM")
        h, mi = int(m.group(1)), int(m.group(2))
        if not (0 <= h <= 23 and 0 <= mi <= 59):
            raise ValueError("hora inválida")
        return f"{h:02d}:{mi:02d}"

    @field_validator("tz")
    @classmethod
    def _tz_ok(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        if not re.match(r"^[A-Za-z0-9_+\-/]{1,64}$", v):
            raise ValueError("fuso IANA inválido")
        return v

    @field_validator("bodies")
    @classmethod
    def _bodies_ok(cls, v):
        if v is None:
            return v
        bad = [b for b in v if b not in TRANSIT_GRID_BODIES]
        if bad:
            raise ValueError(f"corpos em trânsito desconhecidos: {bad}")
        return list(dict.fromkeys(v))

    @field_validator("targets")
    @classmethod
    def _targets_ok(cls, v):
        if v is None:
            return v
        allowed = set(BODY_META) | set(ANGLES)
        bad = [t for t in v if t not in allowed]
        if bad:
            raise ValueError(f"pontos natais desconhecidos: {bad}")
        return list(dict.fromkeys(v))

    @field_validator("extra_natal")
    @classmethod
    def _extra_ok(cls, v):
        bad = [t for t in v if t not in NATAL_BODIES_OPTIONAL]
        if bad:
            raise ValueError(f"corpos opcionais desconhecidos: {bad}")
        return list(dict.fromkeys(v))

    @field_validator("orbs")
    @classmethod
    def _orbs_ok(cls, v):
        if v is None:
            return v
        out = {}
        for k, val in v.items():
            if k not in TRANSIT_GRID_BODIES:
                raise ValueError(f"orbe para corpo desconhecido: {k}")
            fv = float(val)
            if not (0.1 <= fv <= 10.0):
                raise ValueError("orbes devem estar entre 0,1° e 10°")
            out[k] = round(fv, 2)
        return out

    @model_validator(mode="after")
    def _range_ok(self):
        if self.range_from is not None and self.range_to is not None and self.range_to < self.range_from:
            raise ValueError("intervalo invertido")
        if self.range_from is not None and self.range_to is not None and (self.range_to - self.range_from) > 120:
            raise ValueError("intervalo máximo de 120 anos")
        return self

    # ------------------------------------------------------------------ utilidades
    @property
    def year(self) -> int:
        return int(self.date[:4])

    def cache_key(self) -> str:
        payload = json.dumps(self.model_dump(), sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def query_params(self) -> Dict[str, str]:
        """Parâmetros de URL compactos (omite valores padrão)."""
        d = self.model_dump()
        defaults = BirthInput.model_fields
        out: Dict[str, str] = {}
        for k, v in d.items():
            default = defaults[k].default if k in defaults else None
            if v is None or v == default or (isinstance(v, list) and not v):
                continue
            if isinstance(v, bool):
                out[k] = "1" if v else "0"
            elif isinstance(v, list):
                out[k] = ",".join(v)
            elif isinstance(v, dict):
                out[k] = ",".join(f"{a}:{b}" for a, b in v.items())
            else:
                out[k] = str(v)
        # time_known=False precisa ser explícito
        if not self.time_known:
            out["time_known"] = "0"
        return out

    @classmethod
    def from_query(cls, q: Dict[str, str]) -> "BirthInput":
        data: Dict[str, object] = {}
        for k, v in q.items():
            if k in ("bodies", "targets", "extra_natal"):
                data[k] = [x for x in v.split(",") if x]
            elif k == "orbs":
                pairs = [p.split(":") for p in v.split(",") if ":" in p]
                data[k] = {a: float(b) for a, b in pairs}
            elif k in ("time_known", "minors"):
                data[k] = v in ("1", "true", "True", "on")
            elif k in ("lat", "lon"):
                data[k] = float(v)
            elif k in ("range_from", "range_to", "focus_year"):
                data[k] = int(v) if v else None
            else:
                data[k] = v
        return cls(**data)
