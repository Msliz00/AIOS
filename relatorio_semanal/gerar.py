"""Função principal: gerar_relatorio_semanal(expert, data_inicio, data_fim) -> Path."""
from __future__ import annotations

import datetime as dt
import os
from pathlib import Path

from . import criativos, operacao
from .analise import analisar
from .config import get_expert
from .drive import baixar_xlsx
from .render import renderizar
from .textos import montar

RAIZ = Path(__file__).parent
OUT_PADRAO = Path(os.environ.get("RELATORIO_OUT_DIR", RAIZ / "out"))
CACHE_PADRAO = Path(os.environ.get("RELATORIO_CACHE_DIR", RAIZ / "out" / "cache"))


def _obter_planilhas(cfg, xlsx_dir: Path | None, cache_dir: Path) -> tuple[Path, Path]:
    """Usa XLSX locais se `xlsx_dir` for dado; senão baixa do Drive pro cache."""
    nomes = (f"{cfg.slug}_operacao.xlsx", f"{cfg.slug}_criativos.xlsx")
    if xlsx_dir is not None:
        op, cr = (Path(xlsx_dir) / n for n in nomes)
        faltam = [p for p in (op, cr) if not p.exists()]
        if faltam:
            raise FileNotFoundError(f"planilhas locais não encontradas: {faltam}")
        return op, cr
    op = baixar_xlsx(cfg.planilha_operacao_id, cache_dir / nomes[0])
    cr = baixar_xlsx(cfg.planilha_criativos_id, cache_dir / nomes[1])
    return op, cr


def gerar_relatorio_semanal(
    expert: str,
    data_inicio: dt.date,
    data_fim: dt.date,
    *,
    xlsx_dir: Path | str | None = None,
    out_dir: Path | str | None = None,
    cache_dir: Path | str | None = None,
) -> Path:
    """Gera o HTML da semana e devolve o caminho do arquivo.

    1. baixa as 2 planilhas (ou lê de `xlsx_dir`)
    2. soma o diário na janela (cruzando meses) e na janela −7 dias
    3. gate de gasto zero → relatório de semana sem mídia
    4. acha a aba de criativos (match tolerante) e agrega por família/multiplicador
    5. responde as 4 perguntas + top 10, calcula cobertura, renderiza
    """
    cfg = get_expert(expert)
    if isinstance(data_inicio, dt.datetime):
        data_inicio = data_inicio.date()
    if isinstance(data_fim, dt.datetime):
        data_fim = data_fim.date()
    out_dir = Path(out_dir) if out_dir else OUT_PADRAO
    cache_dir = Path(cache_dir) if cache_dir else CACHE_PADRAO

    op_path, cr_path = _obter_planilhas(cfg, Path(xlsx_dir) if xlsx_dir else None, cache_dir)

    semana = operacao.ler_janela(op_path, data_inicio, data_fim)
    anterior = operacao.ler_janela(op_path, data_inicio - dt.timedelta(days=7), data_fim - dt.timedelta(days=7))

    aba = None
    if not semana.sem_midia:  # gate: semana morta não lê criativo
        aba = criativos.ler_semana(cr_path, data_inicio, data_fim)

    analise = analisar(cfg, semana, anterior, aba)
    html = renderizar(cfg, montar(analise))

    out_dir.mkdir(parents=True, exist_ok=True)
    sufixo = "-sem-midia" if semana.sem_midia else ""
    destino = out_dir / f"{cfg.slug}-relatorio-semanal-s{analise.numero_semana:02d}{sufixo}.html"
    destino.write_text(html, encoding="utf-8")
    return destino


def semana_anterior(hoje: dt.date | None = None) -> tuple[dt.date, dt.date]:
    """Segunda→domingo da semana anterior a `hoje` (pro agendador de segunda 8h)."""
    hoje = hoje or dt.date.today()
    segunda_atual = hoje - dt.timedelta(days=hoje.weekday())
    ini = segunda_atual - dt.timedelta(days=7)
    return ini, ini + dt.timedelta(days=6)
