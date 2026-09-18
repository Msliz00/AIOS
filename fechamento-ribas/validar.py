#!/usr/bin/env python3
"""Validador de formulas - substituto do recalc.py quando o LibreOffice nao roda.

Avalia todas as formulas do workbook com a lib 'formulas' e reporta erros
(#DIV/0!, #REF!, #VALUE!, #NAME?, #N/A, #NULL!, #NUM!) — equivalente ao
'total_errors' do recalc.py.

  pip install formulas
  python3 validar.py FECHAMENTO_X.xlsx [--mostrar A1 B2 ...] [--aba "VT UNIFICADO"]
"""
from __future__ import annotations

import argparse
import logging
import re
import sys

logging.disable(logging.WARNING)

ERROS = ("#DIV/0!", "#REF!", "#VALUE!", "#NAME?", "#N/A", "#NULL!", "#NUM!")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("arquivo")
    ap.add_argument("--aba", default=None, help="filtra a exibicao por aba")
    ap.add_argument("--mostrar", nargs="*", default=[], help="celulas para imprimir (ex.: I12)")
    a = ap.parse_args()

    try:
        import formulas
    except ImportError:
        sys.exit("faltou: pip install formulas")

    book = a.arquivo.split("/")[-1]
    sol = formulas.ExcelModel().loads(a.arquivo).finish().calculate()

    def valor(v):
        try:
            return v.value[0, 0]
        except Exception:
            return v

    erros = []
    for chave, bruto in sol.items():
        if "'!" not in chave:
            continue
        v = valor(bruto)
        if isinstance(v, str) and v.strip() in ERROS:
            erros.append((chave, v.strip()))

    abas = sorted({re.search(r"\](.*?)'!", k).group(1) for k in sol if "'!" in k})
    print(f"arquivo    : {book}")
    print(f"abas       : {len(abas)} -> {', '.join(abas)}")
    print(f"celulas    : {len(sol)}")
    print(f"total_errors: {len(erros)}")
    for chave, v in erros[:40]:
        print(f"   {chave} = {v}")

    if a.mostrar:
        alvos = [a.aba.upper()] if a.aba else abas
        for aba in alvos:
            for ref in a.mostrar:
                chave = f"'[{book}]{aba.upper()}'!{ref.upper()}"
                if chave in sol:
                    print(f"   {aba}!{ref.upper()} = {valor(sol[chave])}")

    sys.exit(1 if erros else 0)


if __name__ == "__main__":
    main()
