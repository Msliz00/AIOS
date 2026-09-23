#!/usr/bin/env python3
"""Forense dos exports semanais: de onde cada arquivo tirou a data do nome.

Esses exports nao carregam periodo interno, entao o nome e a unica autoridade
de data - e o nome foi digitado a mao. Este script levanta a evidencia que
existe (metadado de disco, timestamp interno do xlsx, impressao digital do
dado) e responde se a ordem de criacao confere com a ordem das semanas que os
nomes afirmam.

  python3 forense_exports.py "/caminho/da/pasta" [--procurar-em ~/Downloads ~/Desktop]

Nao renomeia, nao move, nao apaga. So le.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import re
import sys
import unicodedata
import zipfile
from pathlib import Path

try:
    from openpyxl import load_workbook
except ImportError:
    sys.exit("faltou: pip install openpyxl")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from roster import BINGO as R_BINGO, REALS as R_REALS

ROSTER = {"BINGO": {b for b, *_ in R_BINGO}, "REALS": {b for b, _ in R_REALS}}
DATA_NOME = re.compile(r"\b(\d{1,2})[:/.\-](\d{1,2})[:/.\-](\d{2,4})\b")
# qualquer coisa com cara de data dentro do arquivo
DATA_DENTRO = re.compile(r"\b\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b")


def _norm(s) -> str:
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode()
    return s.upper()


def _num(v) -> float:
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    t = str(v).strip().replace("R$", "").replace(" ", "")
    if not t:
        return 0.0
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".")
    elif "," in t:
        t = t.replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return 0.0


def plataforma(nome: str) -> str:
    n = _norm(nome)
    return "BINGO" if "BINGO" in n else ("REALS" if "REAL" in n else "?")


def datas_do_nome(nome: str) -> list[dt.date]:
    out = []
    for d, m, a in DATA_NOME.findall(nome):
        ano = int(a) + (2000 if int(a) < 100 else 0)
        try:
            out.append(dt.date(ano, int(m), int(d)))
        except ValueError:
            pass
    return out


def ts(v):
    return dt.datetime.fromtimestamp(v).strftime("%d/%m/%y %H:%M:%S") if v else "-"


def docprops(caminho: Path) -> tuple[str, str]:
    try:
        with zipfile.ZipFile(caminho) as z:
            if "docProps/core.xml" not in z.namelist():
                return "-", "-"
            xml = z.read("docProps/core.xml").decode("utf-8", "ignore")
    except Exception:
        return "-", "-"
    def pega(tag):
        m = re.search(rf"<{tag}[^>]*>([^<]+)</{tag}>", xml)
        return m.group(1).replace("T", " ").replace("Z", "")[:19] if m else "-"
    return pega("dcterms:created"), pega("dcterms:modified")


def periodo_interno(caminho: Path) -> list[str]:
    """Pergunta A: varre TODAS as partes do zip atras de data."""
    achados = []
    try:
        with zipfile.ZipFile(caminho) as z:
            for nome in z.namelist():
                if nome.endswith((".png", ".jpeg", ".jpg", ".bin")):
                    continue
                try:
                    txt = z.read(nome).decode("utf-8", "ignore")
                except Exception:
                    continue
                if nome.startswith("docProps/"):
                    continue          # timestamp de geracao, nao periodo
                for m in set(DATA_DENTRO.findall(txt)):
                    achados.append(f"{nome}: {m}")
    except Exception as e:
        achados.append(f"(nao abriu: {type(e).__name__})")
    return achados[:20]


def medir(caminho: Path, plat: str) -> dict:
    st = caminho.stat()
    criado, modificado = docprops(caminho)
    info = {"nome": caminho.name, "plat": plat,
            "mtime": ts(st.st_mtime),
            "birth": ts(getattr(st, "st_birthtime", None)),
            "dp_criado": criado, "dp_modificado": modificado,
            "bytes": st.st_size, "linhas": 0, "contas": 0,
            "ftd": 0.0, "ngr": 0.0, "r_contas": 0, "r_ftd": 0.0, "r_ngr": 0.0,
            "fp": "", "erro": ""}
    try:
        wb = load_workbook(caminho, data_only=True, read_only=True)
    except Exception as e:
        info["erro"] = f"nao abriu ({type(e).__name__})"
        return info
    ws = wb.worksheets[0]
    cab = []
    for row in ws.iter_rows(min_row=1, max_row=1, values_only=True):
        cab = [_norm(c).replace(" ", "") for c in row]
        break

    def idx(*pre):
        for i, c in enumerate(cab):
            if any(c.startswith(p) for p in pre):
                return i
        return None

    i_c, i_f, i_n = idx("AFFILIATE", "BTAG"), idx("FTD"), idx("NGR")
    if None in (i_c, i_f, i_n):
        info["erro"] = "faltam colunas Affiliate/FTD/NGR"
        wb.close()
        return info

    alvo = ROSTER.get(plat, set())
    h = hashlib.sha256()
    for row in ws.iter_rows(min_row=2, values_only=True):
        info["linhas"] += 1
        if row[i_c] in (None, ""):
            continue
        conta = re.sub(r"\D", "", str(row[i_c])) or str(row[i_c]).strip()
        ftd, ngr = _num(row[i_f]), _num(row[i_n])
        info["contas"] += 1
        info["ftd"] += ftd
        info["ngr"] += ngr
        if conta in alvo:
            info["r_contas"] += 1
            info["r_ftd"] += ftd
            info["r_ngr"] += ngr
        h.update(f"{conta}|{ftd:.2f}|{ngr:.2f}\n".encode())
    wb.close()
    info["fp"] = h.hexdigest()[:12]
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pasta")
    ap.add_argument("--procurar-em", nargs="*", default=[],
                    help="outras pastas onde caçar o arquivo de origem (pergunta E)")
    a = ap.parse_args()

    base = Path(a.pasta).expanduser()
    if not base.is_dir():
        sys.exit(f"pasta nao encontrada: {base}")

    arqs = sorted(p for p in base.iterdir()
                  if p.suffix.lower() in {".xlsx", ".xlsm"} and not p.name.startswith("~$"))
    itens = []
    for p in arqs:
        plat = plataforma(p.name)
        d = medir(p, plat)
        ds = datas_do_nome(p.stem)
        d["ini"] = ds[0] if ds else None
        d["fim"] = ds[-1] if len(ds) > 1 else None
        itens.append(d)

    print(f"PASTA: {base}")
    print(f"ARQUIVOS: {len(itens)}\n")

    print("=" * 110)
    print("1-5. LEVANTAMENTO POR ARQUIVO")
    print("=" * 110)
    for d in itens:
        sem = f"{d['ini']:%d/%m/%y}->{d['fim']:%d/%m/%y}" if d["ini"] and d["fim"] else "sem data no nome"
        print(f"\n  {d['nome']}")
        print(f"    semana no nome : {sem}   ({d['plat']})")
        print(f"    mtime          : {d['mtime']}")
        print(f"    birthtime      : {d['birth']}")
        print(f"    docProps criado: {d['dp_criado']}   modificado: {d['dp_modificado']}")
        if d["erro"]:
            print(f"    ERRO           : {d['erro']}")
            continue
        print(f"    tamanho        : {d['bytes']:,} bytes   linhas: {d['linhas']}")
        print(f"    planilha toda  : {d['contas']} contas, {d['ftd']:.0f} FTD, NGR {d['ngr']:,.2f}")
        print(f"    roster         : {d['r_contas']}/{len(ROSTER.get(d['plat'], ()))}, "
              f"{d['r_ftd']:.0f} FTD, NGR {d['r_ngr']:,.2f}")
        print(f"    impressao      : #{d['fp']}")

    print("\n" + "=" * 110)
    print("A. O EXPORT GUARDA O PERIODO INTERNAMENTE?")
    print("=" * 110)
    amostra = itens[0]
    achados = periodo_interno(base / amostra["nome"])
    print(f"  varredura completa do zip de: {amostra['nome']}")
    if achados:
        for x in achados:
            print(f"    {x}")
    else:
        print("    NAO HA. Nenhuma data em nenhuma parte do arquivo (fora docProps).")
        print("    -> o nome e a unica autoridade de data.")

    print("\n" + "=" * 110)
    print("B/C. A ORDEM DE CRIACAO BATE COM A ORDEM DAS SEMANAS?")
    print("=" * 110)
    for plat in ("BINGO", "REALS"):
        grupo = [d for d in itens if d["plat"] == plat and d["ini"] and d["dp_criado"] != "-"]
        if len(grupo) < 2:
            continue
        print(f"\n  == {plat} ==")
        por_criacao = sorted(grupo, key=lambda d: (d["dp_criado"], d["ini"]))
        print("  ordem de criacao (docProps) -> semana que o nome afirma:")
        # timestamps iguais nao ordenam nada: o lote saiu no mesmo segundo
        distintos = {d["dp_criado"] for d in grupo}
        fora = 0
        anterior_ts = anterior_sem = None
        for i, d in enumerate(por_criacao, 1):
            marca = " "
            # so e desordem quando o timestamp REALMENTE avancou e a semana recuou
            if anterior_ts and d["dp_criado"] > anterior_ts and d["ini"] < anterior_sem:
                marca = "<"
                fora += 1
            print(f"    {i:>2}. {d['dp_criado']}  ->  {d['ini']:%d/%m/%y} {marca}  {d['nome']}")
            if anterior_ts is None or d["dp_criado"] > anterior_ts:
                anterior_ts, anterior_sem = d["dp_criado"], d["ini"]
        if len(distintos) == 1:
            print(f"  INDETERMINADO: os {len(grupo)} arquivos tem o MESMO timestamp de criacao")
            print(f"  ({distintos.pop()}). O lote saiu de uma vez, entao a ordem de download")
            print("  nao existe e nao da para confrontar com a ordem das semanas por aqui.")
        elif fora == 0:
            print(f"  OK: {len(distintos)} timestamps distintos, ordem de criacao == ordem")
            print("  cronologica das semanas. O nome esta coerente com a sequencia de download.")
        else:
            print(f"  ERR: {fora} arquivo(s) fora de ordem (marcados <).")
            print("       O nome foi aplicado fora da sequencia de download - nao e confiavel.")

    print("\n" + "=" * 110)
    print("D/E. CONTEUDO REPETIDO E ARQUIVO DE ORIGEM")
    print("=" * 110)
    por_fp = {}
    for d in itens:
        if d["fp"]:
            por_fp.setdefault(d["fp"], []).append(d["nome"])
    dup = {k: v for k, v in por_fp.items() if len(v) > 1}
    if dup:
        for fp, nomes in dup.items():
            print(f"  ERR #{fp} aparece em {len(nomes)} arquivos DESTA pasta:")
            for n in nomes:
                print(f"       - {n}")
    else:
        print("  nenhuma semana desta pasta repete o dado de outra")

    for outra in getattr(a, "procurar_em", []):
        d_out = Path(outra).expanduser()
        if not d_out.is_dir():
            continue
        print(f"\n  procurando em {d_out} ...")
        for p in sorted(d_out.glob("*.xlsx")):
            if p.name.startswith("~$"):
                continue
            info = medir(p, plataforma(p.name))
            if not info["fp"]:
                continue
            iguais = por_fp.get(info["fp"], [])
            if iguais:
                print(f"    #{info['fp']}  {p.name}")
                print(f"        mesmo dado de: {', '.join(iguais)}")
                print(f"        mtime {info['mtime']} | birth {info['birth']} "
                      f"| docProps {info['dp_criado']}")


if __name__ == "__main__":
    main()
