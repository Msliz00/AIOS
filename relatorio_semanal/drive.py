"""Download das planilhas do Google Drive como XLSX.

Duas portas de entrada:

* `baixar_xlsx(file_id, destino)` — Drive API v3 com service account
  (env `GOOGLE_SERVICE_ACCOUNT_FILE` apontando para o JSON, ou
  `GOOGLE_SERVICE_ACCOUNT_JSON` com o JSON inline). A conta precisa de acesso
  de leitura às duas planilhas.
* `decodificar_download_mcp(payload)` — gotcha #1: o conector MCP do Drive
  devolve o binário como base64 dentro de JSON aninhado. Esta função aceita
  qualquer uma das camadas e devolve os bytes validados.
"""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
MAGIC_ZIP = b"PK\x03\x04"


class DownloadError(RuntimeError):
    pass


def validar_xlsx(dados: bytes) -> bytes:
    if not dados.startswith(MAGIC_ZIP):
        raise DownloadError(
            f"conteúdo não é XLSX (magic bytes {dados[:4]!r}); "
            "provavelmente veio uma camada de JSON ainda por decodificar"
        )
    return dados


def decodificar_download_mcp(payload) -> bytes:
    """Desembrulha o retorno do `download_file_content` do MCP até chegar nos bytes.

    Caminhos aceitos: bytes prontos; string JSON; dict com `content`;
    lista cujo [0]['text'] é uma string JSON com `content`.
    """
    obj = payload
    for _ in range(4):  # no máximo 4 camadas de embrulho
        if isinstance(obj, (bytes, bytearray)):
            return validar_xlsx(bytes(obj))
        if isinstance(obj, list) and obj and isinstance(obj[0], dict) and "text" in obj[0]:
            obj = obj[0]["text"]
            continue
        if isinstance(obj, str):
            s = obj.strip()
            if s.startswith("{") or s.startswith("["):
                obj = json.loads(s)
                continue
            return validar_xlsx(base64.b64decode(s))
        if isinstance(obj, dict) and "content" in obj:
            obj = obj["content"]
            continue
        break
    raise DownloadError(f"formato de payload não reconhecido: {type(payload).__name__}")


def _credenciais():
    try:
        from google.oauth2 import service_account  # type: ignore
    except ImportError as e:  # pragma: no cover - depende do ambiente
        raise DownloadError(
            "google-auth não instalado: pip install -r relatorio_semanal/requirements.txt"
        ) from e
    scopes = ["https://www.googleapis.com/auth/drive.readonly"]
    inline = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    arquivo = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")
    if inline:
        return service_account.Credentials.from_service_account_info(json.loads(inline), scopes=scopes)
    if arquivo:
        return service_account.Credentials.from_service_account_file(arquivo, scopes=scopes)
    raise DownloadError(
        "defina GOOGLE_SERVICE_ACCOUNT_FILE (caminho do JSON) ou GOOGLE_SERVICE_ACCOUNT_JSON"
    )


def baixar_xlsx(file_id: str, destino: Path) -> Path:
    """Exporta uma planilha Google (ou baixa um .xlsx) para `destino`."""
    from google.auth.transport.requests import AuthorizedSession  # type: ignore

    sessao = AuthorizedSession(_credenciais())
    meta = sessao.get(
        f"https://www.googleapis.com/drive/v3/files/{file_id}",
        params={"fields": "mimeType,name", "supportsAllDrives": "true"},
        timeout=60,
    )
    if meta.status_code != 200:
        raise DownloadError(f"metadata {file_id}: HTTP {meta.status_code} {meta.text[:200]}")
    mime = meta.json().get("mimeType", "")
    if mime == "application/vnd.google-apps.spreadsheet":
        r = sessao.get(
            f"https://www.googleapis.com/drive/v3/files/{file_id}/export",
            params={"mimeType": XLSX_MIME},
            timeout=120,
        )
    else:
        r = sessao.get(
            f"https://www.googleapis.com/drive/v3/files/{file_id}",
            params={"alt": "media", "supportsAllDrives": "true"},
            timeout=120,
        )
    if r.status_code != 200:
        raise DownloadError(f"download {file_id}: HTTP {r.status_code} {r.text[:200]}")
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(validar_xlsx(r.content))
    return destino
