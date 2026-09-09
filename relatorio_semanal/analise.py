"""Cruzamento diário × criativos: famílias, as 4 respostas, cobertura e régua."""
from __future__ import annotations

import datetime as dt
import re
from collections import defaultdict
from dataclasses import dataclass, field

from .config import OFERTAS_PADRAO, ExpertConfig, Regua
from .criativos import AbaCriativos, Criativo
from .operacao import Janela

# --------------------------------------------------------------------------
# régua de aceite
# --------------------------------------------------------------------------
def cor_c_lead(v: float | None, r: Regua) -> str:
    if v is None:
        return "neutro"
    return "ok" if v <= r.c_lead_ok else "alerta" if v <= r.c_lead_alerta else "ruim"


def cor_c_reg(v: float | None, r: Regua) -> str:
    if v is None:
        return "neutro"
    return "ok" if v <= r.c_reg_ok else "alerta" if v <= r.c_reg_alerta else "ruim"


def cor_c_ftd(v: float | None, r: Regua) -> str:
    if v is None:
        return "neutro"
    return "ok" if v <= r.c_ftd_ok else "alerta" if v <= r.c_ftd_alerta else "ruim"


def cor_ngr(v: float) -> str:
    return "ok" if v >= 0 else "ruim"


# --------------------------------------------------------------------------
# agregação por família / multiplicador
# --------------------------------------------------------------------------
@dataclass
class Grupo:
    chave: str
    familia: str
    multiplicador: str | None = None
    itens: list[Criativo] = field(default_factory=list)

    @property
    def n(self) -> int:
        return len(self.itens)

    @property
    def investimento(self) -> float:
        return sum(c.investimento for c in self.itens)

    @property
    def leads(self) -> float:
        return sum(c.leads for c in self.itens)

    @property
    def registros(self) -> float:
        return sum(c.registros for c in self.itens)

    @property
    def ftd(self) -> float:
        return sum(c.ftd for c in self.itens)

    @property
    def c_lead(self) -> float | None:
        return self.investimento / self.leads if self.leads else None

    @property
    def c_ftd(self) -> float | None:
        return self.investimento / self.ftd if self.ftd else None


def agrupar(aba: AbaCriativos, cfg: ExpertConfig) -> tuple[list[Grupo], list[Grupo]]:
    """Devolve (por_familia, por_familia_e_multiplicador), ambos ordenados por invest."""
    fam: dict[str, Grupo] = {}
    sub: dict[str, Grupo] = {}
    for c in aba.criativos:
        f = cfg.familia_de(c.nome)
        nome_f = f.nome if f else "Outros"
        fam.setdefault(nome_f, Grupo(nome_f, nome_f)).itens.append(c)
        mult = cfg.multiplicador_de(c.nome) if (f and f.usa_multiplicador) else None
        if f and f.usa_multiplicador:
            chave = f"{nome_f} {mult}" if mult else f"{nome_f} (s/ mult.)"
        else:
            chave = nome_f
        g = sub.setdefault(chave, Grupo(chave, nome_f, mult))
        g.itens.append(c)
    ordem = lambda g: g.investimento
    return (
        sorted(fam.values(), key=ordem, reverse=True),
        sorted(sub.values(), key=ordem, reverse=True),
    )


def ranquear_por_resultado(grupos: list[Grupo]) -> list[Grupo]:
    """Melhores formatos: FTD primeiro, depois menor C/FTD, depois invest."""
    return sorted(
        grupos,
        key=lambda g: (-g.ftd, g.c_ftd if g.c_ftd is not None else float("inf"), -g.investimento),
    )


# --------------------------------------------------------------------------
# resultado completo
# --------------------------------------------------------------------------
@dataclass
class Cobertura:
    invest_criativos: float
    gasto_diario: float
    reg_criativos: float
    reg_diario: float
    ftd_criativos: float
    ftd_diario: float

    @property
    def pct(self) -> float | None:
        return self.invest_criativos / self.gasto_diario if self.gasto_diario else None

    @property
    def pct_ftd_atribuido(self) -> float | None:
        return self.ftd_criativos / self.ftd_diario if self.ftd_diario else None

    @property
    def atribuicao_furada(self) -> bool:
        """Gotcha #5: soma de reg/FTD dos criativos muito abaixo do diário."""
        p = self.pct_ftd_atribuido
        return p is not None and p < 0.5

    @property
    def incoerente(self) -> bool:
        """Aba de criativos que não pode ser desta semana (invest >> diário)."""
        if self.gasto_diario <= 0:
            return self.invest_criativos > 0
        return self.invest_criativos > 1.5 * self.gasto_diario


@dataclass
class Delta:
    campo: str
    atual: float | None
    anterior: float | None

    @property
    def variacao(self) -> float | None:
        if self.atual is None or self.anterior in (None, 0):
            return None
        return (self.atual - self.anterior) / abs(self.anterior)


@dataclass
class Analise:
    cfg: ExpertConfig
    semana: Janela
    anterior: Janela
    aba: AbaCriativos | None
    numero_semana: int
    por_familia: list[Grupo] = field(default_factory=list)
    por_sub: list[Grupo] = field(default_factory=list)
    cobertura: Cobertura | None = None
    top10: list[Criativo] = field(default_factory=list)
    top10_proprios: int = 0
    top10_com_ftd: int = 0
    cta_tem_base: bool = False
    cta_n_marcados: int = 0
    cta_share_invest: float = 0.0
    cta_grupos: list[tuple[str, Grupo]] = field(default_factory=list)
    oferta_tem_sinal: bool = False
    oferta_grupos: list[tuple[str, Grupo]] = field(default_factory=list)
    deltas: dict[str, Delta] = field(default_factory=dict)
    avisos: list[str] = field(default_factory=list)

    @property
    def sem_midia(self) -> bool:
        return self.semana.sem_midia

    @property
    def aba_utilizavel(self) -> bool:
        return self.aba is not None and self.cobertura is not None and not self.cobertura.incoerente


_RX_CTA_TOKENS = [
    ("CTA humanizado", re.compile(r"CTA\s*HUMANIZADO", re.I)),
    ("Com CTA", re.compile(r"COM\s*CTA|\+\s*CTA|\bCTA\b(?!\s*HUMANIZADO)", re.I)),
    ("Sem CTA", re.compile(r"SEM\s*CTA", re.I)),
    ("Com legenda", re.compile(r"COM\s*LEGENDA|LEGENDADO|\+\s*LEGENDA", re.I)),
    ("Sem legenda", re.compile(r"SEM\s*LEGENDA", re.I)),
    ("Hook", re.compile(r"\bHOOK\b", re.I)),
    ("Com música", re.compile(r"COM\s*M[UÚ]SICA", re.I)),
    ("Sem música", re.compile(r"SEM\s*M[UÚ]SICA", re.I)),
]


def _grupos_por_marcador(itens: list[Criativo], tokens) -> list[tuple[str, Grupo]]:
    grupos: dict[str, Grupo] = {}
    for c in itens:
        for rotulo, rx in tokens:
            if rx.search(c.nome):
                grupos.setdefault(rotulo, Grupo(rotulo, rotulo)).itens.append(c)
    return sorted(grupos.items(), key=lambda kv: (-kv[1].ftd, -kv[1].investimento))


def analisar(cfg: ExpertConfig, semana: Janela, anterior: Janela, aba: AbaCriativos | None) -> Analise:
    a = Analise(cfg=cfg, semana=semana, anterior=anterior, aba=aba,
                numero_semana=semana.inicio.isocalendar()[1])

    # deltas vs semana anterior (janela deslocada −7 dias)
    for campo in ("gasto", "leads", "registros", "ftd", "c_lead", "c_reg", "c_ftd", "ngr_menos_gasto"):
        a.deltas[campo] = Delta(campo, getattr(semana, campo), getattr(anterior, campo))

    if semana.abas_faltantes:
        a.avisos.append("Diário sem aba para: " + ", ".join(semana.abas_faltantes))
    if len(semana.dias) < semana.dias_esperados:
        a.avisos.append(
            f"Diário tem {len(semana.dias)} de {semana.dias_esperados} dias da janela preenchidos"
        )

    if semana.sem_midia:
        return a  # gate: semana morta não tem leitura de criativo
    if aba is None:
        a.avisos.append("Aba de criativos da semana não encontrada — análise só com o diário")
        return a

    a.cobertura = Cobertura(
        invest_criativos=aba.investimento, gasto_diario=semana.gasto,
        reg_criativos=aba.registros, reg_diario=semana.registros,
        ftd_criativos=aba.ftd, ftd_diario=semana.ftd,
    )
    if a.cobertura.incoerente:
        a.avisos.append(
            f"Aba '{aba.titulo}' não bate com o diário (invest R$ {aba.investimento:,.0f} vs gasto "
            f"R$ {semana.gasto:,.0f}) — ignorada na análise por peça"
        )
        return a
    if a.cobertura.pct is not None and a.cobertura.pct > 1.02:
        a.avisos.append(
            f"Aba de criativos soma {a.cobertura.pct:.0%} do gasto do diário — diário provavelmente "
            "incompleto na janela (dia sem gasto lançado); C/FTD do diário pode estar subestimado"
        )
    elif a.cobertura.pct is not None and a.cobertura.pct < 0.999:
        a.avisos.append(
            f"Aba de criativos cobre {a.cobertura.pct:.0%} do gasto do diário — "
            "C/FTD por peça tem margem (dia final não detalhado)"
        )
    if a.cobertura.atribuicao_furada:
        a.avisos.append(
            f"Atribuição furada: criativos somam {aba.ftd:.0f} FTD de {semana.ftd:.0f} do diário "
            f"({a.cobertura.pct_ftd_atribuido:.0%}) — C/FTD por peça só como direção"
        )

    a.por_familia, a.por_sub = agrupar(aba, cfg)
    a.top10 = aba.criativos[:10]
    a.top10_proprios = sum(1 for c in a.top10 if cfg.eh_producao_propria(c.nome))
    a.top10_com_ftd = sum(1 for c in a.top10 if c.ftd > 0)

    marcados = [c for c in aba.criativos if cfg.marcadores_cta.search(c.nome)]
    invest_marcado = sum(c.investimento for c in marcados)
    a.cta_n_marcados = len(marcados)
    a.cta_share_invest = invest_marcado / aba.investimento if aba.investimento else 0.0
    # base mínima: 3 peças marcadas e 25% do invest — abaixo disso a leitura seria chute
    a.cta_tem_base = a.cta_n_marcados >= 3 and a.cta_share_invest >= 0.25
    if a.cta_tem_base:
        a.cta_grupos = _grupos_por_marcador(marcados, _RX_CTA_TOKENS)

    com_oferta = [c for c in aba.criativos if cfg.marcadores_oferta.search(c.nome)]
    a.oferta_tem_sinal = bool(com_oferta)
    if a.oferta_tem_sinal:
        a.oferta_grupos = _grupos_por_marcador(com_oferta, cfg.ofertas or OFERTAS_PADRAO)
    return a
