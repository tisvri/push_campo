"""
log_envios.py
Módulo compartilhado de logging para Google Sheets.
Adicione este arquivo na raiz dos dois repositórios.
"""

import os
import json
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials 


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Colunas da planilha (na ordem em que aparecem)
COLUNAS = [
    "timestamp",
    "projeto",
    "grupo",
    "status",        # ENVIADO | PULADO | ERRO
    "destinatarios",
    "num_registros",
    "observacao",
]


def _get_sheet():
    """Autentica e retorna a worksheet de log."""
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    sheet_id   = os.getenv("LOG_SHEET_ID")

    if not creds_json or not sheet_id:
        raise ValueError(
            "Variáveis GOOGLE_CREDENTIALS_JSON e LOG_SHEET_ID são obrigatórias."
        )

    creds = Credentials.from_service_account_info(json.loads(creds_json), scopes=SCOPES)
    client = gspread.authorize(creds)
    sh = client.open_by_key(sheet_id)

    # Cria a aba "log_envios" se não existir
    try:
        ws = sh.worksheet("log_envios")
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title="log_envios", rows=5000, cols=len(COLUNAS))
        ws.append_row(COLUNAS)  # cabeçalho

    return ws


def registrar(projeto: str, grupo: str, status: str,
              destinatarios: list = None, num_registros: int = 0,
              observacao: str = ""):
    """
    Grava uma linha de log na planilha.

    Parâmetros
    ----------
    projeto       : nome do projeto, ex: "Push Campo" ou "Push Monitoria"
    grupo         : grupo de destinatários, ex: "HMCG", "Rocio", "Geral"
    status        : "ENVIADO", "PULADO" ou "ERRO"
    destinatarios : lista de emails que receberam (opcional)
    num_registros : quantidade de registros na tabela enviada
    observacao    : mensagem de erro ou nota adicional
    """
    try:
        ws = _get_sheet()
        linha = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            projeto,
            grupo,
            status,
            ", ".join(destinatarios) if destinatarios else "",
            num_registros,
            observacao,
        ]
        ws.append_row(linha, value_input_option="USER_ENTERED")
    except Exception as e:
        # Não deixa o log quebrar o fluxo principal
        print(f"[log_envios] Falha ao gravar log: {e}")
