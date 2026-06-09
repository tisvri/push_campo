import os
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
sheet_id   = os.getenv("LOG_SHEET_ID")

print(f"GOOGLE_CREDENTIALS_JSON presente: {bool(creds_json)}")
print(f"LOG_SHEET_ID presente: {bool(sheet_id)}")
print(f"LOG_SHEET_ID valor: {sheet_id}")

if not creds_json or not sheet_id:
    raise ValueError("Variáveis ausentes!")

creds  = Credentials.from_service_account_info(json.loads(creds_json), scopes=SCOPES)
client = gspread.authorize(creds)
sh     = client.open_by_key(sheet_id)
print(f"Planilha aberta: {sh.title}")

ws = sh.worksheet("logs")
print(f"Aba 'logs' encontrada com {ws.row_count} linhas")

ws.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "TESTE", "teste_log.py", "ENVIADO", "", 0, "teste manual"])
print("Linha gravada com sucesso!")