"""Configuração por expert.

Trocar de expert = trocar os dois IDs de planilha (e, se precisar, regexes de
família/produção própria e tema). Nada disso vive dentro da função geradora.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Pattern
import re


@dataclass(frozen=True)
class Regua:
    """Tetos de aceite. Verde até `ok`, âmbar até `alerta`, vermelho acima."""

    c_lead_ok: float = 45.0
    c_lead_alerta: float = 55.0
    c_reg_ok: float = 430.0
    c_reg_alerta: float = 430.0 * 55.0 / 45.0  # "idem proporcional" ao C/Lead
    c_ftd_ok: float = 900.0
    c_ftd_alerta: float = 1500.0


@dataclass(frozen=True)
class Tema:
    """Design tokens injetados como variáveis CSS. Trocar cor por expert aqui."""

    accent: str = "#FF6B00"
    accent_soft: str = "#FFE8D6"
    bg: str = "#0F0F10"
    surface: str = "#18181B"
    text: str = "#F5F5F4"
    muted: str = "#A1A1AA"
    font_display: str = "Space Grotesk"
    font_body: str = "Inter"


@dataclass(frozen=True)
class Familia:
    nome: str
    padrao: Pattern[str]
    usa_multiplicador: bool = False


def _rx(p: str) -> Pattern[str]:
    return re.compile(p, re.IGNORECASE)


@dataclass(frozen=True)
class ExpertConfig:
    slug: str
    nome: str
    produto: str
    planilha_operacao_id: str
    planilha_criativos_id: str
    familias: tuple[Familia, ...]
    producao_propria: Pattern[str]
    multiplicador: Pattern[str] = _rx(r"(\d{2,4})\s*X(?![A-Za-z0-9])")
    marcadores_cta: Pattern[str] = _rx(
        r"\bCTA\b|LEGENDA|LEGENDADO|HUMANIZADO|\bHOOK\b|SEM CTA|COM CTA|BASICO|BÁSICO|HEADLINE|HEDLINE"
    )
    marcadores_oferta: Pattern[str] = _rx(
        r"GRUPO|GR[AÁ]TIS|DE\s*GRA[CÇ]A|SAQUE|PROVA|\bVIP\b|BONUS|BÔNUS|DEP[OÓ]SITO|SINAL|SESS[AÃ]O|CORUJ[AÃ]O"
    )
    regua: Regua = Regua()
    tema: Tema = Tema()
    assinatura: str = "00BABY · IGAMING-MASTER-FLOW · Relatório semanal de criativos · +18"

    def familia_de(self, nome: str) -> Familia | None:
        for fam in self.familias:
            if fam.padrao.search(nome):
                return fam
        return None

    def multiplicador_de(self, nome: str) -> str | None:
        m = self.multiplicador.search(nome)
        return f"{int(m.group(1))}X" if m else None

    def eh_producao_propria(self, nome: str) -> bool:
        return bool(self.producao_propria.search(nome))


FAMILIAS_PADRAO: tuple[Familia, ...] = (
    Familia("Corte", _rx(r"CORTE"), usa_multiplicador=True),
    Familia("Gravação de tela", _rx(r"GRAVA\w*\s*DE\s*TELA"), usa_multiplicador=True),
    Familia("Compliance CX", _rx(r"compliance|^CXL_|_CX\d|HOOK_CX")),
    Familia("Caixinha de pergunta", _rx(r"CAIXINHA")),
    Familia("Jogada", _rx(r"JOGADA")),
    Familia("Lista gravada", _rx(r"LISTA\s+GRAVADA")),
    Familia("Roteirizado", _rx(r"ROTEIRIZADO")),
    Familia("RTP", _rx(r"\bRTP\b")),
    Familia("AD numerado", _rx(r"^AD\s*\d+\s*-\s*\d+\s*X"), usa_multiplicador=True),
    Familia("Cria do expert", _rx(r"_Cria_")),
)

EXPERTS: dict[str, ExpertConfig] = {
    "marques": ExpertConfig(
        slug="marques",
        nome="Marques",
        produto="Aviator",
        planilha_operacao_id="1RMt2JDqQSZThYCKaPfBbyWVsFljiQA16m1qLJ38Zqbw",
        planilha_criativos_id="1fBzEB4QtncHeTrRP5D3JzUoTti6sXEVB3B_cTU-omWc",
        familias=FAMILIAS_PADRAO,
        # Lote interno: AD_N_CORTE_..., "AD N - 50X (...)", CXL_ADnn, ADnn_HOOK_CX..
        producao_propria=_rx(r"^(AD[\s_]*\d+|CXL_AD\d+|AD\d+_)"),
    ),
    # Próximos experts: copiar o bloco acima e trocar os dois IDs.
    # "belodi": ExpertConfig(slug="belodi", nome="Belodi", produto="Aviator",
    #     planilha_operacao_id="...", planilha_criativos_id="...",
    #     familias=FAMILIAS_PADRAO, producao_propria=_rx(r"^AD")),
}


def get_expert(slug: str) -> ExpertConfig:
    try:
        return EXPERTS[slug.lower()]
    except KeyError:
        raise KeyError(f"expert '{slug}' não configurado; disponíveis: {sorted(EXPERTS)}") from None
