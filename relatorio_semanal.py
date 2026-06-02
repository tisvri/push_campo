"""
relatorio_semanal.py
Lê o log do Google Sheets e envia email de resumo semanal.
Adicione este arquivo em UM dos repositórios (ou num repositório dedicado).
"""

import os
import json
import smtplib
import gspread
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.oauth2.service_account import Credentials


# ── Configurações ─────────────────────────────────────────────────────────────

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SMTP_SERVER   = os.getenv("EMAIL_SERVER")
SMTP_PORT     = int(os.getenv("EMAIL_PORT", "587").strip())
EMAIL_USUARIO = os.getenv("EMAIL_USERNAME")
EMAIL_SENHA   = os.getenv("EMAIL_PASSWORD")
RELATORIO_PARA = os.getenv("RELATORIO_PARA")  # seu email pessoal

BADGE = {
    "ENVIADO": '<span style="background:#d4edda;color:#155724;padding:3px 10px;border-radius:4px;font-size:11px;font-weight:600;">✓ ENVIADO</span>',
    "PULADO":  '<span style="background:#fff3cd;color:#856404;padding:3px 10px;border-radius:4px;font-size:11px;font-weight:600;">— PULADO</span>',
    "ERRO":    '<span style="background:#f8d7da;color:#721c24;padding:3px 10px;border-radius:4px;font-size:11px;font-weight:600;">✕ ERRO</span>',
}


# ── Leitura do Sheets ─────────────────────────────────────────────────────────

def carregar_logs_semana():
    """Retorna registros dos últimos 7 dias como lista de dicts."""
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    sheet_id   = os.getenv("LOG_SHEET_ID")

    creds  = Credentials.from_service_account_info(json.loads(creds_json), scopes=SCOPES)
    client = gspread.authorize(creds)
    ws     = client.open_by_key(sheet_id).worksheet("logs")

    registros = ws.get_all_records()  # lista de dicts com cabeçalho como chave

    limite = datetime.now() - timedelta(days=7)
    recentes = [
        r for r in registros
        if datetime.strptime(r["timestamp"], "%Y-%m-%d %H:%M:%S") >= limite
    ]
    return recentes


# ── Montagem do relatório ─────────────────────────────────────────────────────

def montar_tabela_html(registros):
    """Gera a tabela HTML com os registros da semana."""
    if not registros:
        return "<p style='color:#666;font-style:italic;'>Nenhum envio registrado nos últimos 7 dias.</p>"

    linhas = ""
    for i, r in enumerate(registros):
        bg = "#ffffff" if i % 2 == 0 else "#f4f8f0"
        badge = BADGE.get(r.get("status", ""), r.get("status", ""))
        obs = r.get("observacao", "") or "—"
        dest = r.get("destinatarios", "") or "—"
        num  = r.get("num_registros", 0)

        linhas += f"""
        <tr style="background:{bg};">
            <td style="padding:9px 12px;border-bottom:1px solid #dde8d4;color:#333;font-size:12px;">{r.get("timestamp","")}</td>
            <td style="padding:9px 12px;border-bottom:1px solid #dde8d4;color:#333;font-size:12px;font-weight:500;">{r.get("projeto","")}</td>
            <td style="padding:9px 12px;border-bottom:1px solid #dde8d4;color:#333;font-size:12px;">{r.get("grupo","")}</td>
            <td style="padding:9px 12px;border-bottom:1px solid #dde8d4;font-size:12px;">{badge}</td>
            <td style="padding:9px 12px;border-bottom:1px solid #dde8d4;color:#555;font-size:12px;">{num}</td>
            <td style="padding:9px 12px;border-bottom:1px solid #dde8d4;color:#555;font-size:12px;">{dest}</td>
            <td style="padding:9px 12px;border-bottom:1px solid #dde8d4;color:#888;font-size:12px;">{obs}</td>
        </tr>"""

    return f"""
    <table style="width:100%;border-collapse:collapse;font-family:Arial,sans-serif;">
        <thead>
            <tr>
                <th style="background:#3B6D11;color:#fff;padding:10px 12px;text-align:left;font-size:11px;letter-spacing:0.03em;">Data/Hora</th>
                <th style="background:#3B6D11;color:#fff;padding:10px 12px;text-align:left;font-size:11px;letter-spacing:0.03em;">Projeto</th>
                <th style="background:#3B6D11;color:#fff;padding:10px 12px;text-align:left;font-size:11px;letter-spacing:0.03em;">Grupo</th>
                <th style="background:#3B6D11;color:#fff;padding:10px 12px;text-align:left;font-size:11px;letter-spacing:0.03em;">Status</th>
                <th style="background:#3B6D11;color:#fff;padding:10px 12px;text-align:left;font-size:11px;letter-spacing:0.03em;">Registros</th>
                <th style="background:#3B6D11;color:#fff;padding:10px 12px;text-align:left;font-size:11px;letter-spacing:0.03em;">Destinatários</th>
                <th style="background:#3B6D11;color:#fff;padding:10px 12px;text-align:left;font-size:11px;letter-spacing:0.03em;">Observação</th>
            </tr>
        </thead>
        <tbody>{linhas}</tbody>
    </table>"""


def montar_resumo(registros):
    """Gera contadores de resumo."""
    total   = len(registros)
    enviados = sum(1 for r in registros if r.get("status") == "ENVIADO")
    pulados  = sum(1 for r in registros if r.get("status") == "PULADO")
    erros    = sum(1 for r in registros if r.get("status") == "ERRO")
    return total, enviados, pulados, erros


def enviar_relatorio():
    registros = carregar_logs_semana()
    total, enviados, pulados, erros = montar_resumo(registros)
    tabela = montar_tabela_html(registros)

    semana = datetime.now().strftime("%d/%m/%Y")
    cor_erro = "#f8d7da" if erros > 0 else "#d4edda"
    txt_erro = f'<span style="color:#721c24;font-weight:600;">{erros} erro(s)</span>' if erros > 0 else f'<span style="color:#155724;">{erros} erros</span>'

    body = f"""
    <html>
    <body style="font-family:Arial,sans-serif;background:#f4f6f4;padding:24px;">
        <div style="background:#fff;border-radius:8px;padding:28px 32px;max-width:900px;margin:0 auto;border:1px solid #dde8d4;">

            <div style="border-bottom:1px solid #dde8d4;padding-bottom:16px;margin-bottom:20px;">
                <h2 style="margin:0 0 4px;font-size:17px;color:#1a2e1a;">Relatório Semanal de Envios</h2>
                <p style="margin:0;font-size:12px;color:#6b7b6b;">Semana até {semana} &mdash; últimos 7 dias</p>
            </div>

            <div style="display:flex;gap:16px;margin-bottom:24px;">
                <div style="flex:1;background:#f4f8f0;border-radius:6px;padding:14px 18px;border:1px solid #dde8d4;">
                    <p style="margin:0 0 4px;font-size:11px;color:#6b7b6b;text-transform:uppercase;letter-spacing:0.05em;">Total</p>
                    <p style="margin:0;font-size:24px;font-weight:700;color:#1a2e1a;">{total}</p>
                </div>
                <div style="flex:1;background:#d4edda;border-radius:6px;padding:14px 18px;border:1px solid #b8dac2;">
                    <p style="margin:0 0 4px;font-size:11px;color:#155724;text-transform:uppercase;letter-spacing:0.05em;">Enviados</p>
                    <p style="margin:0;font-size:24px;font-weight:700;color:#155724;">{enviados}</p>
                </div>
                <div style="flex:1;background:#fff3cd;border-radius:6px;padding:14px 18px;border:1px solid #ffe08a;">
                    <p style="margin:0 0 4px;font-size:11px;color:#856404;text-transform:uppercase;letter-spacing:0.05em;">Pulados</p>
                    <p style="margin:0;font-size:24px;font-weight:700;color:#856404;">{pulados}</p>
                </div>
                <div style="flex:1;background:{cor_erro};border-radius:6px;padding:14px 18px;border:1px solid #f1b0b7;">
                    <p style="margin:0 0 4px;font-size:11px;color:#721c24;text-transform:uppercase;letter-spacing:0.05em;">Erros</p>
                    <p style="margin:0;font-size:24px;font-weight:700;color:#721c24;">{erros}</p>
                </div>
            </div>

            {tabela}

            <div style="border-top:1px solid #dde8d4;padding-top:16px;margin-top:20px;">
                <p style="font-size:12px;color:#6b7b6b;margin:0;">
                    Relatório gerado automaticamente pelo sistema de monitoramento &mdash; <strong>BI SVRI</strong>.
                </p>
            </div>
        </div>
    </body>
    </html>"""

    msg = MIMEMultipart("alternative")
    msg["From"]    = EMAIL_USUARIO
    
    msg["Subject"] = f"[Monitoramento] Relatório Semanal de Envios — {semana}"
    msg.attach(MIMEText(body, "html"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_USUARIO, EMAIL_SENHA)
        destinatarios_relatorio = [e.strip() for e in RELATORIO_PARA.split(",") if e.strip()]
    msg["To"] = ", ".join(destinatarios_relatorio)
    server.sendmail(EMAIL_USUARIO, destinatarios_relatorio, msg.as_string())

    print(f"Relatório enviado para {RELATORIO_PARA} — {enviados} enviados, {pulados} pulados, {erros} erros.")


if __name__ == "__main__":
    enviar_relatorio()