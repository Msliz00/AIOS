"""CLI: python -m relatorio_semanal marques 2026-08-24 2026-08-31 [--xlsx-dir DIR] [--out DIR]

Sem datas → semana anterior (segunda→domingo), que é o que o agendador chama.
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys

from .gerar import gerar_relatorio_semanal, semana_anterior


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="relatorio_semanal")
    p.add_argument("expert")
    p.add_argument("data_inicio", nargs="?", type=dt.date.fromisoformat)
    p.add_argument("data_fim", nargs="?", type=dt.date.fromisoformat)
    p.add_argument("--xlsx-dir", help="lê XLSX locais em vez de baixar do Drive")
    p.add_argument("--out", help="pasta de saída")
    a = p.parse_args(argv)
    if (a.data_inicio is None) != (a.data_fim is None):
        p.error("informe as duas datas ou nenhuma")
    if a.data_inicio is None:
        a.data_inicio, a.data_fim = semana_anterior()
    destino = gerar_relatorio_semanal(a.expert, a.data_inicio, a.data_fim, xlsx_dir=a.xlsx_dir, out_dir=a.out)
    print(destino)
    return 0


if __name__ == "__main__":
    sys.exit(main())
