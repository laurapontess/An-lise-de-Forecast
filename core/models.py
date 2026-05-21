from dataclasses import dataclass, field
from typing import Any


@dataclass
class SDRContext:
    nome: str
    senioridade: str
    meta_net_revenue: float
    meta_sqls: int
    mes_referencia: str


@dataclass
class AnalysisResults:
    analise1: dict = field(default_factory=dict)
    analise2: dict = field(default_factory=dict)
    analise3: dict = field(default_factory=dict)
    analise4: dict = field(default_factory=dict)
