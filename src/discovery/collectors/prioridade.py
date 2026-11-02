"""Prioridade das páginas internas, em português e em inglês."""

from __future__ import annotations

PRIORITY_KEYWORDS = (
    # português
    "sobre", "quem-somos", "quem somos", "institucional", "empresa",
    "servico", "serviço", "solucao", "solução", "produto", "locacao", "locação",
    "aluguel", "frota", "equipamento", "contato", "fale-conosco",
    "privacidade", "termo", "politica", "política", "lgpd",
    # inglês
    "about", "company", "institutional", "service", "solution", "product",
    "rental", "fleet", "equipment", "contact", "privacy", "terms", "policy",
)


def pontuar(url: str, ancora: str = "") -> int:
    """Soma as palavras-chave presentes na URL e no texto do link."""
    texto = f"{url} {ancora}".lower()
    return sum(1 for palavra in PRIORITY_KEYWORDS if palavra in texto)
