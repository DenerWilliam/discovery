"""Formato comum dos dados brutos gravados em ``raw.json``."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

FORMAT_VERSION = 2

OK = "ok"
FALHA = "falha"
NAO_COLETADA = "nao_coletada"
AMBIGUA = "ambigua"

# Motivo classificado de uma falha de acesso, para não depender do texto do erro.
RECUSADO = "recusado"  # 403/429: o servidor recusou o acesso
FALHOU = "falhou"  # 5xx: o servidor respondeu com erro
SEM_RESPOSTA = "sem_resposta"  # tempo esgotado ou erro de conexão


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


@dataclass
class Source:
    tipo: str  # "site" | "cnpj" | "busca"
    origem: str  # URL ou API consultada
    status: str
    coletado_em: str = field(default_factory=now_iso)
    conteudo: Any = None
    erro: str | None = None
    motivo: str | None = None  # recusado | falhou | sem_resposta

    def to_dict(self) -> dict[str, Any]:
        return {
            "tipo": self.tipo,
            "origem": self.origem,
            "coletado_em": self.coletado_em,
            "status": self.status,
            "erro": self.erro,
            "motivo": self.motivo,
            "conteudo": self.conteudo,
        }
