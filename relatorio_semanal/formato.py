"""Formatação PT-BR para o relatório."""
from __future__ import annotations


def brl(v: float | None, casas: int = 0) -> str:
    if v is None:
        return "—"
    s = f"{abs(v):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{'-' if v < 0 else ''}R$ {s}"


def brl_k(v: float | None) -> str:
    if v is None:
        return "—"
    if abs(v) >= 1000:
        return f"{'-' if v < 0 else ''}R$ {abs(v)/1000:.1f}k".replace(".", ",")
    return brl(v)


def inteiro(v: float | None) -> str:
    return "—" if v is None else f"{v:,.0f}".replace(",", ".")


def pct(v: float | None, casas: int = 0) -> str:
    return "—" if v is None else f"{v*100:.{casas}f}%".replace(".", ",")


def delta(v: float | None, invertido: bool = False) -> str:
    """Variação relativa com sinal. `invertido` = queda é boa (custos)."""
    if v is None:
        return "sem base"
    seta = "▲" if v > 0 else "▼" if v < 0 else "="
    return f"{seta} {abs(v)*100:.0f}%"


def classe_delta(v: float | None, invertido: bool = False) -> str:
    if v is None or v == 0:
        return "neutro"
    bom = v < 0 if invertido else v > 0
    return "ok" if bom else "ruim"


def data_br(d) -> str:
    return d.strftime("%d/%m")


def periodo(ini, fim) -> str:
    return f"{data_br(ini)}–{data_br(fim)}/{fim.year}"
