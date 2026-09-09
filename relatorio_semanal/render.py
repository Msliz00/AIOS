"""Renderização do HTML via Jinja2. Só preenche conteúdo — o design vive no template."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .config import ExpertConfig
from .textos import Conteudo

TEMPLATES = Path(__file__).parent / "templates"


def renderizar(cfg: ExpertConfig, conteudo: Conteudo) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html", "j2"]))
    tpl = env.get_template("relatorio.html.j2")
    return tpl.render(
        c=conteudo,
        tema=cfg.tema,
        assinatura=cfg.assinatura,
        gerado_em=dt.datetime.now().strftime("%d/%m/%Y %H:%M"),
    )
