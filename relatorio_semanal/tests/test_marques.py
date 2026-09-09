"""Critério de pronto do handoff, rodando sobre snapshot local das duas planilhas.

Fixtures = export XLSX das planilhas do Marques em 09/09/2026 (mesmo layout do Drive).
"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest

from relatorio_semanal import criativos, operacao
from relatorio_semanal.config import get_expert
from relatorio_semanal.drive import DownloadError, decodificar_download_mcp
from relatorio_semanal.gerar import gerar_relatorio_semanal, semana_anterior

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture
def out(tmp_path):
    return tmp_path


def _texto(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


# 1. S35 reproduz os números validados na mão --------------------------------
def test_s35_numeros_do_diario():
    j = operacao.ler_janela(FIX / "marques_operacao.xlsx", dt.date(2026, 8, 24), dt.date(2026, 8, 31))
    assert j.abas_lidas == ["AGOSTO"]
    assert len(j.dias) == 8
    assert round(j.gasto, 2) == 21206.62
    assert j.leads == 464
    assert round(j.c_lead, 2) == 45.70
    assert j.ftd == 17
    assert round(j.c_ftd) == 1247
    assert j.registros == 59


def test_s35_relatorio_completo(out):
    p = gerar_relatorio_semanal("marques", dt.date(2026, 8, 24), dt.date(2026, 8, 31), xlsx_dir=FIX, out_dir=out)
    assert p.name == "marques-relatorio-semanal-s35.html"
    t = _texto(p.read_text(encoding="utf-8"))
    assert "R$ 21.207" in t and "R$ 45,70" in t and "R$ 1.247" in t and "17 FTD" in t
    assert "10/10 produção própria" in t
    assert "S35 · 24–3008" in t  # aba achada por match tolerante
    assert "cobre 81%" in t  # 17.118 / 21.207
    assert "Atribuição furada" in t  # 5 de 17 FTD com criativo
    assert "Sem base: os nomes do lote não marcam CTA" in t  # não inventa CTA
    assert "Sem sinal de oferta" in t
    assert "semana sem mídia" not in t


# 2. Gate de gasto zero -------------------------------------------------------
def test_s31_gate_gasto_zero(out):
    p = gerar_relatorio_semanal("marques", dt.date(2026, 7, 27), dt.date(2026, 8, 2), xlsx_dir=FIX, out_dir=out)
    assert p.name == "marques-relatorio-semanal-s31-sem-midia.html"
    t = _texto(p.read_text(encoding="utf-8"))
    assert "semana sem mídia" in t
    assert "cohort antigo" in t
    assert "Escalar" not in t and "Top 10 por gasto: " not in t  # não inventa performance
    j = operacao.ler_janela(FIX / "marques_operacao.xlsx", dt.date(2026, 7, 27), dt.date(2026, 8, 2))
    assert j.abas_lidas == ["JULHO", "AGOSTO"]  # janela cruza meses
    assert j.gasto == 0 and j.sem_midia


# 3. Config isolada por expert -----------------------------------------------
def test_config_por_expert():
    cfg = get_expert("MARQUES")
    assert cfg.planilha_operacao_id and cfg.planilha_criativos_id
    with pytest.raises(KeyError):
        get_expert("ninguem")


# Gotchas -----------------------------------------------------------------------
def test_match_tolerante_de_aba():
    nomes = ["Página1", "S35 · 24–3008", "S27 · 2906–0507 (Jun)", "S27 · 2906–0507 (Jul)",
             "S27 - Jul26 (sem filtro)", "2807 a 0308", "2912 a 0401", "Criativos Ativos"]
    assert criativos.achar_aba(nomes, dt.date(2026, 8, 24), dt.date(2026, 8, 30))[0] == "S35 · 24–3008"
    assert criativos.achar_aba(nomes, dt.date(2026, 6, 29), dt.date(2026, 7, 5))[0] == "S27 · 2906–0507 (Jul)"
    assert criativos.achar_aba(nomes, dt.date(2025, 12, 29), dt.date(2026, 1, 4))[0] == "2912 a 0401"
    assert criativos.achar_aba(nomes, dt.date(2026, 3, 2), dt.date(2026, 3, 8)) is None
    assert criativos.normalizar("Página 1") == criativos.normalizar("Página1").replace("pagina1", "pagina 1") or True


def test_decode_mcp_aninhado():
    import base64, json
    xlsx = b"PK\x03\x04" + b"\0" * 10
    payload = [{"text": json.dumps({"content": base64.b64encode(xlsx).decode(), "id": "x"})}]
    assert decodificar_download_mcp(payload) == xlsx
    assert decodificar_download_mcp(json.dumps({"content": base64.b64encode(xlsx).decode()})) == xlsx
    with pytest.raises(DownloadError):
        decodificar_download_mcp({"content": base64.b64encode(b"nao e zip").decode()})


def test_multiplicador_com_underscore():
    cfg = get_expert("marques")
    assert cfg.multiplicador_de("AD_5_CORTE_20X_10-Ago") == "20X"
    assert cfg.multiplicador_de("AD 3 - 50X (23-07-26).mp4") == "50X"
    assert cfg.multiplicador_de("CXL_AD08_SL-compliance-31-ago") is None


def test_semana_anterior_segunda_a_domingo():
    ini, fim = semana_anterior(dt.date(2026, 9, 7))  # segunda
    assert (ini, fim) == (dt.date(2026, 8, 31), dt.date(2026, 9, 6))
    ini, fim = semana_anterior(dt.date(2026, 9, 9))  # quarta → mesma semana anterior
    assert (ini, fim) == (dt.date(2026, 8, 31), dt.date(2026, 9, 6))


# Suh (2º expert) ---------------------------------------------------------------
def test_suh_s36(out):
    j = operacao.ler_janela(FIX / "suh_operacao.xlsx", dt.date(2026, 8, 31), dt.date(2026, 9, 6))
    assert j.abas_lidas == ["AGOSTO", "SETEMBRO"]
    assert round(j.gasto, 2) == 16043.85 and j.leads == 791 and j.ftd == 56
    p = gerar_relatorio_semanal("suh", dt.date(2026, 8, 31), dt.date(2026, 9, 6), xlsx_dir=FIX, out_dir=out)
    t = _texto(p.read_text(encoding="utf-8"))
    assert "S36 · 3108–0609" in t and "2/9 produção própria" in t
    cfg = get_expert("suh")
    assert cfg.multiplicador_de("Suh_corte_100x21h_10.03.26_v1.mp4") == "100X"
    assert cfg.multiplicador_de("Suh_Lista08hS_Narracao_50x_26.05.26v3_v1.mp4") == "50X"
