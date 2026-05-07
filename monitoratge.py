import os
import json
import requests
import gspread
from bs4 import BeautifulSoup
from datetime import datetime
from google.oauth2.service_account import Credentials

# =========================
# CONFIGURACIÓN
# =========================

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1ilj1N5U4pgtI7nIcM2vkUu06dEbrx_vWux4DNz7E_j4/edit?gid=0#gid=0"

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
GOOGLE_CREDENTIALS_JSON = os.environ["GOOGLE_CREDENTIALS_JSON"]

# =========================
# CONEXIÓN GOOGLE SHEETS
# =========================

def connectar_google_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    info = json.loads(GOOGLE_CREDENTIALS_JSON)
    creds = Credentials.from_service_account_info(info, scopes=scopes)

    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_url(SPREADSHEET_URL)
    return spreadsheet.sheet1

sheet = connectar_google_sheet()

# =========================
# TELEGRAM
# =========================

def enviar_telegram(missatge):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": missatge
    }

    response = requests.post(url, data=payload, timeout=30)
    response.raise_for_status()

# =========================
# SCRAPING
# =========================

def revisar_url(url, paraules_clau, paraules_excloses):
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(" ", strip=True).lower()

    claus = [p.strip().lower() for p in str(paraules_clau).split(",") if p.strip()]
    excloses = [p.strip().lower() for p in str(paraules_excloses).split(",") if p.strip()]

    trobades = [p for p in claus if p in text]
    bloquejades = [p for p in excloses if p in text]

    if bloquejades:
        return False, "", f"Descartada per paraules excloses: {', '.join(bloquejades)}"

    if len(trobades) >= 2:
        return True, url, f"Paraules trobades: {', '.join(trobades)}"

    return False, "", f"Coincidències insuficients: {', '.join(trobades) if trobades else 'cap'}"

# =========================
# MAIN
# =========================

def executar_monitoratge():
    registres = sheet.get_all_records()
    updates = []
    noves_detectades = 0

    for index, fila in enumerate(registres, start=2):

        if not any(fila.values()):
            continue

        nom = fila.get("nom", "")
        url = fila.get("url", "")
        paraules_clau = fila.get("paraules_clau", "")
        paraules_excloses= fila.get("paraules_excloses","")
        estat_anterior = fila.get("estat", "")
        activa = str(fila.get("activa", "")).strip().lower()

        if activa not in ["si", "sí", "yes", "y"]:
            print(f"⏭️ {nom}: desactivada")
            continue

        if not nom or not url or not paraules_clau:
            print(f"⚠️ Fila {index}: dades incompletes")
            continue

        avui = datetime.now().strftime("%Y-%m-%d %H:%M")

        try:
            publicada, enllac_bases, observacions = revisar_url(url, paraules_clau, paraules_excloses)
            nou_estat = "PUBLICADA" if publicada else "NO TROBADA"

            print(f"{nom}: {nou_estat}")

            updates.append({
                "range": f"E{index}:I{index}",
                "values": [[
                    nou_estat,        # E estat
                    activa,           # F activa
                    avui,             # G ultima_revisio
                    enllac_bases,     # H enllac_bases
                    observacions      # I observacions
                ]]
            })

            if publicada and estat_anterior != "PUBLICADA":
                noves_detectades +=1
                missatge = f"""📢 CONVOCATÒRIA DETECTADA

Nom: {nom}
Enllaç: {enllac_bases}

{observacions}
"""
                enviar_telegram(missatge)
                print("📩 Missatge enviat a Telegram")

        except Exception as e:
            print(f"❌ Error a {nom}: {e}")

            updates.append({
                "range": f"E{index}:I{index}",
                "values": [[
                    "ERROR",
                    activa,
                    avui,
                    "",
                    str(e)
                ]]
            })

    if updates:
        sheet.batch_update(updates)
        print("✅ Google Sheet actualitzat en bloc")

    if noves_detectades == 0:
        enviar_telegram("✅ Monitoratge executat\nCap nova convocatòria detectada")
    else:
        enviar_telegram(f"✅ Monitoratge executat\n{noves_detectades} noves convocatòries detectades")

# =========================
# RUN
# =========================

if __name__ == "__main__":
    executar_monitoratge()
