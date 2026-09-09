"""Leitura em texto (regra-based) a partir da análise. Nunca inventa número."""
from __future__ import annotations

from dataclasses import dataclass, field

from . import formato as f
from .analise import Analise, Grupo, cor_c_ftd, cor_c_lead, cor_c_reg, cor_ngr


@dataclass
class Card:
    rotulo: str
    valor: str
    cor: str
    sub: str = ""


@dataclass
class Resposta:
    numero: str
    titulo: str
    veredito: str
    corpo: list[str] = field(default_factory=list)
    tag: str = "neutro"


@dataclass
class LinhaTabela:
    grupo: str
    n: int
    invest: str
    c_lead: str
    ftd: str
    c_ftd: str
    status: str
    status_cor: str


@dataclass
class Conteudo:
    eyebrow: str
    titulo: str
    resumo: str
    cards: list[Card]
    contexto: str
    respostas: list[Resposta]
    tabela: list[LinhaTabela]
    tabela_nota: str
    alerta_titulo: str
    alerta: list[str]
    proximos: list[str]
    avisos: list[str]
    sem_midia: bool


def _status_grupo(g: Grupo, regua) -> tuple[str, str]:
    if g.ftd == 0:
        return ("Sem FTD", "ruim" if g.investimento > 300 else "neutro")
    cor = cor_c_ftd(g.c_ftd, regua)
    return ({"ok": "Escalar", "alerta": "Manter", "ruim": "Rever"}[cor], cor)


def _cards(a: Analise) -> list[Card]:
    s, r = a.semana, a.cfg.regua
    return [
        Card("Gasto", f.brl(s.gasto), "neutro", f"{s.dias_com_gasto}/{s.dias_esperados} dias com mídia"),
        Card("C/FTD", f.brl(s.c_ftd, 0), cor_c_ftd(s.c_ftd, r), f"{f.inteiro(s.ftd)} FTD · teto {f.brl(r.c_ftd_ok)}"),
        Card("C/Lead", f.brl(s.c_lead, 2), cor_c_lead(s.c_lead, r), f"{f.inteiro(s.leads)} leads · teto {f.brl(r.c_lead_ok)}"),
        Card("NGR − Gasto", f.brl(s.ngr_menos_gasto), cor_ngr(s.ngr_menos_gasto), f"NGR {f.brl(s.ngr)} · Dep {f.brl(s.deposito)}"),
    ]


def _contexto(a: Analise) -> str:
    s, p, d = a.semana, a.anterior, a.deltas
    if p.gasto <= 0:
        return (
            f"Semana anterior ({f.periodo(p.inicio, p.fim)}) sem mídia — sem base de comparação. "
            f"Registros: {f.inteiro(s.registros)} (C/Reg {f.brl(s.c_reg)}) · "
            f"Reg→FTD {f.pct(s.pct_reg_ftd)}."
        )
    return (
        f"Vs semana anterior ({f.periodo(p.inicio, p.fim)}): gasto {f.delta(d['gasto'].variacao)}, "
        f"leads {f.delta(d['leads'].variacao)}, FTD {f.delta(d['ftd'].variacao)}, "
        f"C/Lead {f.delta(d['c_lead'].variacao)}, C/FTD {f.delta(d['c_ftd'].variacao)}. "
        f"Registros: {f.inteiro(s.registros)} (C/Reg {f.brl(s.c_reg)}, anterior {f.brl(p.c_reg)}) · "
        f"Reg→FTD {f.pct(s.pct_reg_ftd)} (anterior {f.pct(p.pct_reg_ftd)})."
    )


def _resposta_formato(a: Analise) -> Resposta:
    r = Resposta("01", "Melhores formatos", "", tag="neutro")
    if not a.aba_utilizavel:
        r.veredito = "Sem aba de criativos utilizável nesta semana."
        r.corpo = ["Leitura por formato depende da aba semanal. Ver avisos."]
        return r
    from .analise import ranquear_por_resultado

    rank = ranquear_por_resultado(a.por_sub)
    com_ftd = [g for g in rank if g.ftd > 0]
    if not com_ftd:
        r.veredito = "Nenhum formato gerou FTD atribuído na aba."
        r.tag = "ruim"
        maior = a.por_sub[0] if a.por_sub else None
        if maior:
            r.corpo.append(f"Maior gasto: {maior.chave} ({f.brl(maior.investimento)}, C/Lead {f.brl(maior.c_lead, 2)}).")
        return r
    lider = com_ftd[0]
    r.veredito = f"{lider.chave}: {f.inteiro(lider.ftd)} FTD a {f.brl(lider.c_ftd)} (C/Lead {f.brl(lider.c_lead, 2)})."
    r.tag = cor_c_ftd(lider.c_ftd, a.cfg.regua)
    for g in com_ftd[1:3]:
        r.corpo.append(f"{g.chave}: {f.inteiro(g.ftd)} FTD a {f.brl(g.c_ftd)} · {g.n} peças · {f.brl(g.investimento)}.")
    sem = [g for g in a.por_sub if g.ftd == 0 and g.investimento >= 300]
    if sem:
        r.corpo.append("Sem FTD apesar do gasto: " + ", ".join(f"{g.chave} ({f.brl(g.investimento)})" for g in sem[:4]) + ".")
    fams = [g for g in a.por_familia]
    if len(fams) == 1:
        r.corpo.append(f"100% do lote é {fams[0].familia} — ranking é entre multiplicadores, não entre formatos.")
    return r


def _resposta_oferta(a: Analise) -> Resposta:
    r = Resposta("02", "Melhores ofertas", "")
    if not a.aba_utilizavel:
        r.veredito = "Sem aba de criativos utilizável nesta semana."
        return r
    if not a.oferta_tem_sinal:
        r.veredito = "Sem sinal de oferta nos nomes do lote."
        r.tag = "alerta"
        r.corpo = [
            "Nenhuma peça marca grupo grátis, prova de saque, VIP ou bônus no nome — não dá pra ranquear oferta.",
            "Buraco: falta ângulo de oferta explícito (grupo grátis / prova de saque) no lote.",
        ]
        return r
    top = a.oferta_grupos[0]
    if top[1].ftd:
        r.veredito = f"{top[0]}: {f.inteiro(top[1].ftd)} FTD a {f.brl(top[1].c_ftd)} · {f.brl(top[1].investimento)}."
        r.tag = cor_c_ftd(top[1].c_ftd, a.cfg.regua)
    else:
        r.veredito = "Ofertas marcadas no nome não geraram FTD atribuído."
        r.tag = "alerta"
        r.corpo.append(f"{top[0]}: 0 FTD · {top[1].n} peças · {f.brl(top[1].investimento)} · C/Lead {f.brl(top[1].c_lead, 2)}.")
    for rot, g in a.oferta_grupos[1:4]:
        r.corpo.append(f"{rot}: {f.inteiro(g.ftd)} FTD · {g.n} peças · {f.brl(g.investimento)}.")
    return r


def _resposta_cta(a: Analise) -> Resposta:
    r = Resposta("03", "Melhores CTAs", "")
    if not a.aba_utilizavel:
        r.veredito = "Sem aba de criativos utilizável nesta semana."
        return r
    if not a.cta_tem_base:
        r.veredito = "Sem base: os nomes do lote não marcam CTA/legenda."
        r.tag = "alerta"
        exemplo = a.aba.criativos[0].nome if a.aba and a.aba.criativos else ""
        r.corpo = [
            f"Padrão de nome atual (ex.: {exemplo}) não carrega CTA, legenda nem hook — qualquer leitura seria inventada.",
            "Recomendação: remarcar no nome (ex.: _CTAHUM / _SEMCTA / _LEG) antes do próximo lote.",
        ]
        return r
    top = a.cta_grupos[0]
    if top[1].ftd:
        r.veredito = f"{top[0]}: {f.inteiro(top[1].ftd)} FTD a {f.brl(top[1].c_ftd)} · {f.brl(top[1].investimento)} · C/Lead {f.brl(top[1].c_lead, 2)}."
        r.tag = cor_c_ftd(top[1].c_ftd, a.cfg.regua)
    else:
        r.veredito = "Nenhuma variação de CTA marcada gerou FTD — leitura só por C/Lead."
        r.tag = "alerta"
    for rot, g in a.cta_grupos[1:5]:
        r.corpo.append(f"{rot}: {f.inteiro(g.ftd)} FTD · {g.n} peças · {f.brl(g.investimento)} · C/Lead {f.brl(g.c_lead, 2)}.")
    r.corpo.append(f"Base: {a.cta_n_marcados} peças com marcador no nome ({f.pct(a.cta_share_invest)} do invest da aba); o resto do lote não marca CTA.")
    return r


def _resposta_top10(a: Analise) -> Resposta:
    r = Resposta("04", "Top 10 por gasto", "")
    if not a.aba_utilizavel:
        r.veredito = "Sem aba de criativos utilizável nesta semana."
        return r
    n = len(a.top10)
    r.veredito = f"{a.top10_proprios}/{n} produção própria · {a.top10_com_ftd}/{n} geraram FTD."
    r.tag = "ok" if a.top10_com_ftd >= n / 2 else "alerta" if a.top10_com_ftd else "ruim"
    for c in a.top10:
        marca = "●" if a.cfg.eh_producao_propria(c.nome) else "○"
        r.corpo.append(
            f"{marca} {c.nome} — {f.brl(c.investimento)} · {f.inteiro(c.leads)} leads · "
            f"{f.inteiro(c.ftd)} FTD" + (f" ({f.brl(c.c_ftd)})" if c.ftd else "")
        )
    r.corpo.append("● = produção própria · ○ = não identificado como produção própria")
    return r


def _tabela(a: Analise) -> tuple[list[LinhaTabela], str]:
    if not a.aba_utilizavel:
        return [], "Sem aba de criativos utilizável — tabela vazia."
    linhas = []
    for g in a.por_sub:
        status, cor = _status_grupo(g, a.cfg.regua)
        linhas.append(LinhaTabela(g.chave, g.n, f.brl(g.investimento), f.brl(g.c_lead, 2),
                                  f.inteiro(g.ftd), f.brl(g.c_ftd), status, cor))
    cob = a.cobertura
    nota = f"Aba '{a.aba.titulo}' ({a.aba.motivo_match}) · {len(a.aba.criativos)} peças · cobre {f.pct(cob.pct)} do gasto do diário"
    if cob.atribuicao_furada:
        nota += f" · atribuição: {f.inteiro(cob.ftd_criativos)} de {f.inteiro(cob.ftd_diario)} FTD com criativo ({f.pct(cob.pct_ftd_atribuido)}) — C/FTD por peça só como direção"
    return linhas, nota + "."


def _alerta(a: Analise) -> tuple[str, list[str]]:
    s, r = a.semana, a.cfg.regua
    itens = []
    if s.c_ftd is not None and s.c_ftd > r.c_ftd_alerta:
        itens.append(f"C/FTD {f.brl(s.c_ftd)} acima do teto de alerta ({f.brl(r.c_ftd_alerta)}).")
    elif s.c_ftd is not None and s.c_ftd > r.c_ftd_ok:
        itens.append(f"C/FTD {f.brl(s.c_ftd)} acima do teto ({f.brl(r.c_ftd_ok)}).")
    if s.c_lead is not None and s.c_lead > r.c_lead_ok:
        itens.append(f"C/Lead {f.brl(s.c_lead, 2)} acima do teto ({f.brl(r.c_lead_ok)}).")
    if s.ngr_menos_gasto < 0:
        itens.append(f"NGR − Gasto negativo em {f.brl(s.ngr_menos_gasto)}.")
    if a.aba_utilizavel and a.por_familia:
        lider = a.por_familia[0]
        share = lider.investimento / a.aba.investimento if a.aba.investimento else 0
        if share >= 0.7:
            itens.append(f"Concentração: {f.pct(share)} do investimento em {lider.familia} — risco de fadiga de formato.")
        if a.top10 and a.top10_com_ftd <= 3:
            itens.append(f"Só {a.top10_com_ftd} dos {len(a.top10)} maiores gastos geraram FTD.")
        for g in a.por_sub:
            share_g = g.investimento / a.aba.investimento if a.aba.investimento else 0
            if share_g >= 0.15 and (g.ftd == 0 or cor_c_ftd(g.c_ftd, r) == "ruim"):
                itens.append(
                    f"{g.chave} leva {f.pct(share_g)} do investimento "
                    + ("sem FTD atribuído." if g.ftd == 0 else f"a {f.brl(g.c_ftd)} por FTD.")
                )
        if a.cobertura and a.cobertura.atribuicao_furada:
            itens.append(f"Só {f.pct(a.cobertura.pct_ftd_atribuido)} dos FTD têm criativo atribuído — ranking por peça é direção, não veredito.")
    if s.dias_com_gasto < s.dias_esperados:
        itens.append(f"Mídia rodou em {s.dias_com_gasto} de {s.dias_esperados} dias.")
    if not itens:
        itens.append("Nenhum teto estourado nesta semana.")
    return ("Risco da semana", itens)


def _proximos(a: Analise) -> list[str]:
    s, passos = a.semana, []
    if a.aba_utilizavel:
        from .analise import ranquear_por_resultado

        rank = [g for g in ranquear_por_resultado(a.por_sub) if g.ftd > 0]
        if rank:
            lider, cor = rank[0], cor_c_ftd(rank[0].c_ftd, a.cfg.regua)
            if cor == "ok":
                passos.append(f"Escalar {lider.chave} (C/FTD {f.brl(lider.c_ftd)}, dentro do teto).")
            elif cor == "alerta":
                passos.append(f"Manter {lider.chave} sem escalar (C/FTD {f.brl(lider.c_ftd)}, acima do teto de {f.brl(a.cfg.regua.c_ftd_ok)}).")
            else:
                passos.append(f"Não escalar nada: melhor grupo é {lider.chave} a {f.brl(lider.c_ftd)} por FTD — trocar hook/oferta antes de subir verba.")
        mortos = [g for g in a.por_sub if g.ftd == 0 and g.investimento >= 500]
        if mortos:
            passos.append("Pausar ou trocar hook em: " + ", ".join(g.chave for g in mortos[:3]) + ".")
        if not a.cta_tem_base:
            passos.append("Padronizar nome dos criativos com marcador de CTA/legenda pra próxima leitura ter base.")
        if not a.oferta_tem_sinal:
            passos.append("Subir pelo menos 2 peças com ângulo de oferta (grupo grátis / prova de saque).")
        if a.cobertura and a.cobertura.atribuicao_furada:
            passos.append("Fechar a atribuição de registro/FTD por criativo na planilha — hoje a maior parte dos FTD não tem peça.")
        if len(a.por_familia) == 1:
            passos.append("Testar 1 formato fora de " + a.por_familia[0].familia + " pra ter contraste na próxima semana.")
    else:
        passos.append("Criar/ajustar a aba semanal de criativos pra próxima rodada ter leitura por peça.")
    if s.c_lead and s.c_lead > a.cfg.regua.c_lead_ok:
        passos.append(f"Trazer C/Lead pra baixo de {f.brl(a.cfg.regua.c_lead_ok)} (hoje {f.brl(s.c_lead, 2)}).")
    return passos[:6]


def montar(a: Analise) -> Conteudo:
    s = a.semana
    n = a.numero_semana
    eyebrow = f"{a.cfg.nome} · {a.cfg.produto} · Relatório semanal"
    if a.sem_midia:
        return Conteudo(
            eyebrow=eyebrow,
            titulo=f"S{n} · {f.periodo(s.inicio, s.fim)} — semana sem mídia",
            resumo=(
                f"A semana pedida ({f.periodo(s.inicio, s.fim)}) não rodou: gasto zero em "
                f"{s.dias_esperados} dias ({s.dias_com_gasto} com mídia). Não há performance de criativo pra ler. "
                f"Os {f.inteiro(s.ftd)} FTD e {f.brl(s.deposito)} de depósito do período são colheita de cohort "
                f"antigo, não resultado da semana."
            ),
            cards=[
                Card("Gasto", f.brl(0), "ruim", f"0/{s.dias_esperados} dias com mídia"),
                Card("FTD (cohort antigo)", f.inteiro(s.ftd), "neutro", "sem mídia atribuível"),
                Card("Depósito (cohort antigo)", f.brl(s.deposito), "neutro", "colheita de semanas anteriores"),
                Card("NGR", f.brl(s.ngr), cor_ngr(s.ngr), "sem gasto no período"),
            ],
            contexto=(
                f"Semana anterior ({f.periodo(a.anterior.inicio, a.anterior.fim)}): gasto {f.brl(a.anterior.gasto)}, "
                f"{f.inteiro(a.anterior.ftd)} FTD."
                if a.anterior.gasto > 0 else
                f"Semana anterior ({f.periodo(a.anterior.inicio, a.anterior.fim)}) também sem mídia."
            ),
            respostas=[
                Resposta(str(i), t, "Sem base — semana sem mídia.", ["Nenhum criativo rodou com gasto nesta janela."], "neutro")
                for i, t in (("01", "Melhores formatos"), ("02", "Melhores ofertas"), ("03", "Melhores CTAs"), ("04", "Top 10 por gasto"))
            ],
            tabela=[],
            tabela_nota="Sem leitura por formato: gasto zero na janela.",
            alerta_titulo="Gasto zerado",
            alerta=[f"Mídia parada nos {s.dias_esperados} dias da janela. Depósito/FTD do período não valida nenhum criativo."],
            proximos=[
                "Confirmar com a operação o motivo da pausa (conta, verba ou decisão).",
                "Religar mídia com o último lote validado antes de testar peça nova.",
                "Rodar o relatório de novo na semana seguinte com gasto ativo.",
            ],
            avisos=a.avisos,
            sem_midia=True,
        )

    respostas = [_resposta_formato(a), _resposta_oferta(a), _resposta_cta(a), _resposta_top10(a)]
    tabela, nota = _tabela(a)
    alerta_t, alerta = _alerta(a)
    resumo = (
        f"Gasto {f.brl(s.gasto)} em {s.dias_com_gasto} dias · {f.inteiro(s.leads)} leads a {f.brl(s.c_lead, 2)} · "
        f"{f.inteiro(s.registros)} registros · {f.inteiro(s.ftd)} FTD a {f.brl(s.c_ftd)} · "
        f"NGR − Gasto {f.brl(s.ngr_menos_gasto)}. "
    )
    if a.aba_utilizavel and a.top10:
        resumo += f"Top 10 por gasto: {a.top10_proprios}/{len(a.top10)} produção própria, {a.top10_com_ftd} com FTD."
    elif a.aba is None:
        resumo += "Sem aba de criativos pra esta semana."
    return Conteudo(
        eyebrow=eyebrow,
        titulo=f"S{n} · {f.periodo(s.inicio, s.fim)}",
        resumo=resumo,
        cards=_cards(a),
        contexto=_contexto(a),
        respostas=respostas,
        tabela=tabela,
        tabela_nota=nota,
        alerta_titulo=alerta_t,
        alerta=alerta,
        proximos=_proximos(a),
        avisos=a.avisos,
        sem_midia=False,
    )
