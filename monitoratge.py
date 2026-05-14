import os
import json
import requests
import gspread
from bs4 import BeautifulSoup
from datetime import datetime
from google.oauth2.service_account import Credentials
from urllib.parse import urljoin

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

def obtenir_pdfs(soup, base_url):
    pdfs = []

    for link in soup.find_all("a", href=True):
        href = link["href"].strip()

        if ".pdf" in href.lower():
            pdf_url = urljoin(base_url, href)
            pdfs.append(pdf_url)

    return sorted(set(pdfs))
def revisar_url(url, paraules_clau, paraules_excloses, pdfs_anteriors):
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(
        url,
        headers=headers,
        timeout=30,
        allow_redirects=True
    )
    response.raise_for_status()

    url_final = response.url
    if url_final.rstrip("/") != url.rstrip("/"):
        raise Exception(f"La URL redirigeix a una altra pàgina: {url_final}")
        
    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(" ", strip=True).lower()

    claus = [p.strip().lower() for p in str(paraules_clau).split(",") if p.strip()]
    excloses = [p.strip().lower() for p in str(paraules_excloses).split(",") if p.strip()]

    any_actual = str(datetime.now().year)
    if any_actual not in claus:
        claus.append(any_actual)

    trobades = [p for p in claus if p in text]
    bloquejades = [p for p in excloses if p in text]

    pdfs_actuals = obtenir_pdfs(soup, url_final)
    pdfs_antics = [p.strip() for p in str(pdfs_anteriors).split("\n") if p.strip()]
    pdfs_nous = [p for p in pdfs_actuals if p not in pdfs_antics]

    observacions_parts = []

    if url_final.rstrip("/") != url.rstrip("/"):
        observacions_parts.append(f"Redirect detectat: {url_final}")

    if trobades:
        observacions_parts.append(f"Paraules trobades: {', '.join(trobades)}")
    else:
        observacions_parts.append("Paraules trobades: cap")

    if pdfs_nous:
        observacions_parts.append(f"PDFs nous detectats: {len(pdfs_nous)}")

    if bloquejades:
        observacions_parts.append(f"Paraules excloses trobades: {', '.join(bloquejades)}")
        return False, "", " | ".join(observacions_parts), pdfs_actuals, pdfs_nous

    publicada = len(trobades) >= 2 or len(pdfs_nous) > 0

    if publicada:
        enllac_bases = pdfs_nous[0] if pdfs_nous else url_final
        return True, enllac_bases, " | ".join(observacions_parts), pdfs_actuals, pdfs_nous

    observacions_parts.append("No compleix criteris de detecció")
    return False, "", " | ".join(observacions_parts), pdfs_actuals, pdfs_nous
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
        pdfs_anteriors = fila.get("pdfs_detectats","")
        area_oncologica = fila.get("area_oncologica", "")
        subespecialitzacio = fila.get("subespecialitzacio", "")
        tema = fila.get("tema", "")
        tipus_convocatoria = fila.get("tipus_convocatoria", "")
        ambit = fila.get("ambit", "")
        perfil_elegible = fila.get("perfil_elegible", "")
        multicentric = fila.get("multicentric", "")
        financament = fila.get("financament", "")
        durada_anys = fila.get("durada_anys", "")
        notes_estrategiques = fila.get("notes_estrategiques", "")

        if activa not in ["si", "sí", "yes", "y"]:
            print(f"⏭️ {nom}: desactivada")
            continue

        if not nom or not url or not paraules_clau:
            print(f"⚠️ Fila {index}: dades incompletes")
            continue

        avui = datetime.now().strftime("%Y-%m-%d %H:%M")

        try:
            publicada, enllac_bases, observacions, pdfs_actuals, pdfs_nous = revisar_url(url, paraules_clau, paraules_excloses,pdfs_anteriors)
            nou_estat = "PUBLICADA" if publicada else "NO TROBADA"

            print(f"{nom}: {nou_estat}")

            updates.append({
                "range": f"E{index}:K{index}",
                "values": [[
                    nou_estat,        # E estat
                    activa,           # F activa
                    avui,             # G ultima_revisio
                    enllac_bases,     # H enllac_bases
                    observacions,     # I observacions
                    paraules_excloses, # J paraules_excloses
                    "\n".join(pdfs_actuals) # pdfs_detectats
                ]]
            })

            if publicada and estat_anterior != "PUBLICADA":
                noves_detectades +=1
                missatge = f"""📢 CONVOCATÒRIA DETECTADA

Nom: {nom}
Àrea oncològica: {area_oncologica}
Subespecialització: {subespecialitzacio}
Tema: {tema}
Tipus convocatòria: {tipus_convocatoria}
Àmbit: {ambit}
Perfil elegible: {perfil_elegible}
Multicèntric: {multicentric}
Finançament: {financament}
Durada: {durada_anys} anys

Enllaç: {enllac_bases}

Detecció:
{observacions}

Notes:
{notes_estrategiques}
"""
                enviar_telegram(missatge)
                print("📩 Missatge enviat a Telegram")

        except Exception as e:
            print(f"❌ Error a {nom}: {e}")

            updates.append({
                "range": f"E{index}:K{index}",
                "values": [[
                    "ERROR",
                    activa,
                    avui,
                    "",
                    str(e),
                    paraules_excloses,
                    pdfs_anteriors
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
