#!/usr/bin/env python3
"""Converte o backup do CRM antigo nos CSVs de import de leads_master.

Uso: python3 preparar_import.py <dir_do_backup> [dir_saida]

Gera:
  import_crm.csv       telefone,nome,email,origem,origem_detalhe,optin_sms,optin_ligacao
  import_telegram.csv  telegram_id,telegram_username,nome,origem,origem_detalhe

Regras:
  - telefone vira E.164 BR (mesma logica de public.normalizar_telefone)
  - dedup por telefone normalizado, mantendo o registro mais completo
  - optin_* so e true com consent_marketing e sem opt_out. Ninguem entra com
    optin_telegram: esse consentimento so nasce do /start no bot.
"""
import csv, re, sys, os

def norm(t):
    d = re.sub(r'\D', '', t or '')
    if 10 <= len(d) <= 11:
        return '55' + d
    if len(d) == 14 and d.startswith('550'):
        return '55' + d[3:]
    return d or None

def preparar_crm(origem, destino):
    best, descartados = {}, 0
    with open(origem, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            n = norm(r['telefone'] or r['telefone_bruto'])
            if not n or len(n) not in (12, 13):
                descartados += 1
                continue
            score = sum(1 for k in ('nome', 'email', 'origem', 'btag') if r.get(k))
            if n not in best or score > best[n][0]:
                best[n] = (score, r)

    with open(destino, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['telefone', 'nome', 'email', 'origem', 'origem_detalhe',
                    'optin_sms', 'optin_ligacao'])
        for n, (_, r) in best.items():
            consent = r['consent_marketing'] == 't' and r['opt_out'] != 't'
            w.writerow([n, r['nome'] or '', r['email'] or '',
                        r['origem'] or 'crm_base_fria', r['btag'] or '',
                        'true' if (consent and r['apto_sms'] == 't') else 'false',
                        'true' if consent else 'false'])
    return len(best), descartados

def preparar_telegram(origem, destino):
    n = 0
    with open(origem, newline='', encoding='utf-8') as g, \
         open(destino, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['telegram_id', 'telegram_username', 'nome', 'origem', 'origem_detalhe'])
        for r in csv.DictReader(g):
            if not r['telegram_id']:
                continue
            w.writerow([r['telegram_id'], r['username'] or '', r['primeiro_nome'] or '',
                        'telegram_grupo', r['grupo_origem'] or ''])
            n += 1
    return n

if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else '.'
    out = sys.argv[2] if len(sys.argv) > 2 else src
    leads, descartados = preparar_crm(os.path.join(src, 'crm_base_fria.csv'),
                                      os.path.join(out, 'import_crm.csv'))
    tg = preparar_telegram(os.path.join(src, 'leads.csv'),
                           os.path.join(out, 'import_telegram.csv'))
    print(f'import_crm.csv       {leads} leads unicos ({descartados} descartados)')
    print(f'import_telegram.csv  {tg} leads')
