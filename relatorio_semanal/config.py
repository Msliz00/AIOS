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
    # rótulos de oferta lidos do nome (rótulo, regex); None = OFERTAS_PADRAO
    ofertas: tuple[tuple[str, Pattern[str]], ...] | None = None
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


OFERTAS_PADRAO: tuple[tuple[str, Pattern[str]], ...] = (
    ("Grupo grátis", _rx(r"GRUPO.*GR[AÁ]TIS|GR[AÁ]TIS|DE\s*GRA[CÇ]A")),
    ("Prova (saque / social)", _rx(r"SAQUE|PROVA")),
    ("VIP", _rx(r"\bVIP\b")),
    ("Bônus / depósito", _rx(r"BONUS|BÔNUS|DEP[OÓ]SITO")),
    ("Sessão / sinal", _rx(r"SESS[AÃ]O|SINAL|CORUJ[AÃ]O")),
)

FAMILIAS_PADRAO: tuple[Familia, ...] = (
    Familia("Corte", _rx(r"CORTE"), usa_multiplicador=True),
    Familia("Gravação de tela", _rx(r"GRAVA\w*\s*DE\s*TELA"), usa_multiplicador=True),
    Familia("Compliance CX", _rx(r"compliance|^CXL_|_CX\d|HOOK_CX")),
    Familia("Caixinha de pergunta", _rx(r"CAIXINHA")),
    Familia("Jogada", _rx(r"JOGADA")),
    Familia("Lista gravada", _rx(r"LISTA\s+GRAVADA")),
    Familia("Lista (horário)", _rx(r"LISTA\s*\d{1,2}H|\d+X\s*LISTA\s*\d{1,2}H"), usa_multiplicador=True),
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
    "suh": ExpertConfig(
        slug="suh",
        nome="Suh",
        produto="Aviator",
        planilha_operacao_id="16DKJ-dG8eA-XEjxNwEyYZN5jUCiYrPlyAYDG9_PzRlI",
        planilha_criativos_id="10-NSZ2aYlkjMxiNQCOgDwTwoOoFPdXH-SrN-3k-CvEQ",
        familias=(
            Familia("Gravação de tela", _rx(r"GRAVA\w*\s*DE\s*TELA|Gravaodetela"), usa_multiplicador=True),
            Familia("Lista (horário)", _rx(r"LISTA\s*\d{1,2}H|\d+X\s*LISTA\s*\d{1,2}H"), usa_multiplicador=True),
            Familia("Corte", _rx(r"CORTE"), usa_multiplicador=True),
            Familia("Jogada", _rx(r"JOGADA"), usa_multiplicador=True),
            Familia("Variação A/B", _rx(r"^\d+X\s*VAR\d"), usa_multiplicador=True),
        ) + FAMILIAS_PADRAO,
        # "100xCorujao": multiplicador colado em texto → só exige não vir dígito depois
        multiplicador=_rx(r"(?<![0-9])(\d{2,4})\s*X"),
        # HIPÓTESE a confirmar: lote nosso = variações JOGADA_50X_SUH_VARn / "50X VARn - …";
        # "Suh_…_dd.mm.aa_vN" é o padrão da equipe do expert.
        producao_propria=_rx(r"JOGADA_\d+X_SUH|^\d+X\s*VAR\d|_VAR\d"),
        marcadores_cta=_rx(
            r"\bCTA\b|LEGENDA|LEGENDADO|HUMANIZADO|\bHOOK\b|SEM CTA|COM CTA|BASICO|BÁSICO|HEADLINE|HEDLINE|M[UÚ]SICA"
        ),
        ofertas=(
            ("Corujão (sessão da madrugada)", _rx(r"CORUJ[AÃ]O")),
            ("Max Win", _rx(r"MAX\s*WIN")),
            ("Lista com horário (08h/16h/21h/23h)", _rx(r"LISTA\s*\d{1,2}H|\d{1,2}H\b")),
        ) + tuple(o for o in OFERTAS_PADRAO if o[0] != "Sessão / sinal"),
    ),
    # Próximos experts: copiar um bloco acima e trocar os dois IDs.
    # "belodi": ExpertConfig(slug="belodi", nome="Belodi", produto="Aviator",
    #     planilha_operacao_id="...", planilha_criativos_id="...",
    #     familias=FAMILIAS_PADRAO, producao_propria=_rx(r"^AD")),
}


def get_expert(slug: str) -> ExpertConfig:
    try:
        return EXPERTS[slug.lower()]
    except KeyError:
        raise KeyError(f"expert '{slug}' não configurado; disponíveis: {sorted(EXPERTS)}") from None
