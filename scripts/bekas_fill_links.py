#!/usr/bin/env python3
"""Preenche a coluna LINK (C) da planilha BEKAS a partir de um mapeamento nome -> link.

Auth: service account (Google Sheets API v4).
  - GOOGLE_SA_FILE=/caminho/sa.json   (ou)
  - GOOGLE_SA_JSON='{"type":"service_account",...}'
A planilha precisa estar compartilhada (Editor) com o e-mail da service account.

Uso:
  python3 scripts/bekas_fill_links.py \
      --sheet-id 1IpISy5pq1vimkKGqx-KNfj3QX-CKg786vfSy6XW_l2g \
      --tab MARQUES --tab "MEDIANO E EXCELENTE" \
      --mapping scripts/bekas_links_s36.json [--dry-run] [--overwrite]

Regras:
  - casa a coluna A (Nome) com as chaves do mapeamento, ignorando caixa, espacos,
    extensao .mp4 e trocando '/' por '-' (Drive usa '/', planilha usa '-');
  - so escreve onde C esta vazio, salvo --overwrite;
  - --tab casa por substring no titulo da aba (case-insensitive).
"""
import argparse
import json
import os
import re
import sys

import requests
from google.auth.transport.requests import Request
from google.oauth2 import service_account

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
API = "https://sheets.googleapis.com/v4/spreadsheets"


def norm(name: str) -> str:
    s = (name or "").strip().lower()
    s = re.sub(r"\.(mp4|mov)$", "", s)
    s = s.replace("/", "-")
    s = re.sub(r"\s+", " ", s)
    return s


def token() -> str:
    raw = os.environ.get("GOOGLE_SA_JSON")
    path = os.environ.get("GOOGLE_SA_FILE")
    if raw:
        creds = service_account.Credentials.from_service_account_info(json.loads(raw), scopes=SCOPES)
    elif path:
        creds = service_account.Credentials.from_service_account_file(path, scopes=SCOPES)
    else:
        sys.exit("Defina GOOGLE_SA_JSON ou GOOGLE_SA_FILE")
    creds.refresh(Request())
    return creds.token


def sheets_get(sess, sheet_id, params):
    r = sess.get(f"{API}/{sheet_id}", params=params)
    r.raise_for_status()
    return r.json()


def values_get(sess, sheet_id, rng):
    r = sess.get(f"{API}/{sheet_id}/values/{requests.utils.quote(rng, safe='')}")
    r.raise_for_status()
    return r.json().get("values", [])


def values_batch_update(sess, sheet_id, data):
    body = {"valueInputOption": "RAW", "data": data}
    r = sess.post(f"{API}/{sheet_id}/values:batchUpdate", json=body)
    r.raise_for_status()
    return r.json()


def a1_tab(title: str) -> str:
    return "'" + title.replace("'", "''") + "'"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet-id", required=True)
    ap.add_argument("--tab", action="append", required=True, help="substring do titulo da aba (repetivel)")
    ap.add_argument("--mapping", required=True, help="JSON {nome: link}")
    ap.add_argument("--name-col", default="A")
    ap.add_argument("--link-col", default="C")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    with open(args.mapping, encoding="utf-8") as f:
        mapping = {norm(k): v for k, v in json.load(f).items()}

    sess = requests.Session()
    sess.headers["Authorization"] = f"Bearer {token()}"

    meta = sheets_get(sess, args.sheet_id, {"fields": "sheets.properties(sheetId,title)"})
    titles = [s["properties"]["title"] for s in meta["sheets"]]

    total_written = 0
    for want in args.tab:
        matches = [t for t in titles if want.lower() in t.lower()]
        if not matches:
            print(f"[{want}] aba nao encontrada. Abas: {titles}")
            continue
        for title in matches:
            names = values_get(sess, args.sheet_id, f"{a1_tab(title)}!{args.name_col}:{args.name_col}")
            links = values_get(sess, args.sheet_id, f"{a1_tab(title)}!{args.link_col}:{args.link_col}")
            updates, skipped, missing = [], [], []
            for i, row in enumerate(names):
                if i == 0 or not row:
                    continue
                key = norm(row[0])
                if key not in mapping:
                    if row[0].strip():
                        missing.append(row[0])
                    continue
                current = links[i][0].strip() if i < len(links) and links[i] else ""
                if current and not args.overwrite:
                    skipped.append((i + 1, row[0]))
                    continue
                updates.append({"range": f"{a1_tab(title)}!{args.link_col}{i + 1}", "values": [[mapping[key]]]})
            print(f"\n== {title}: {len(updates)} a escrever, {len(skipped)} ja preenchidas, {len(missing)} sem mapeamento")
            for u in updates:
                print("  ", u["range"], "->", u["values"][0][0])
            if updates and not args.dry_run:
                res = values_batch_update(sess, args.sheet_id, updates)
                total_written += res.get("totalUpdatedCells", 0)
    print(f"\nCelulas escritas: {total_written}{' (dry-run)' if args.dry_run else ''}")


if __name__ == "__main__":
    main()
