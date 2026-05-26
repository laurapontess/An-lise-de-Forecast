from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SDRContext:
    nome: str
    senioridade: str          # "Júnior" ou "Pleno"
    meta_net_revenue: float   # Meta NR em R$
    meta_sqls: int            # Meta de SQLs (Closed Won)
    mes_referencia: str       # Ex: "Maio/2025"
